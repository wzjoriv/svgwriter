"""
PDF file structure: the object lexer, streams and filters, the page tree and content operations.
"""

from __future__ import annotations

import re
import zlib
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from ._constants import (
    DEFAULT_MEDIABOX,
    ENDSTREAM_RE,
    FLATE,
    INLINE_IMAGE_END_RE,
    LITERALS,
    NAME_ESCAPE_RE,
    OBJECT_RE,
    PDF_MAX_DEPTH,
    PDF_TOKEN_RE,
    STREAM_RE,
)
from ._reading import string_end

__all__ = ["Name", "Operator", "Ref", "Stream"]


class Name(str):
    """A PDF name object such as ``/Type``, without the slash."""


class Operator(str):
    """A bare keyword: a content-stream operator."""


@dataclass(frozen=True)
class Ref:
    """An indirect reference ``N G R``."""

    number: int


@dataclass
class Stream:
    """A stream object: its dictionary and its still-encoded bytes."""

    info: dict[str, Any]
    raw: bytes


class _Lexer:
    """Tokens and values of PDF syntax, starting at *pos*."""

    def __init__(self, data: bytes, pos: int = 0) -> None:
        self.data, self.pos = data, pos

    def token(self) -> tuple[str, bytes] | None:
        """The next token as ``(kind, text)``, or None at the end."""
        while (match := PDF_TOKEN_RE.match(self.data, self.pos)) is not None:
            self.pos = match.end()
            if match.lastgroup == "string":
                self.pos = string_end(self.data, self.pos)
                return "string", self.data[match.end():self.pos - 1]
            if match.lastgroup != "skip":
                return match.lastgroup or "other", match.group()
        return None

    def value(self, token: tuple[str, bytes], refs: bool = False) -> Any:
        """The object that starts with *token*; ``N G R`` becomes a :class:`Ref` when *refs*."""
        kind, text = token
        if kind == "num":
            number = float(text) if b"." in text else int(text)
            return self._ref(number) if refs and isinstance(number, int) else number
        if kind == "name":
            return Name(NAME_ESCAPE_RE.sub(lambda m: bytes.fromhex(m.group(1).decode()), text[1:]).decode("latin-1"))
        if kind == "hex":
            digits = re.sub(rb"\s", b"", text[1:-1]).decode("latin-1")
            return bytes.fromhex(digits + "0" * (len(digits) % 2))
        if kind == "string":
            return text
        if text == b"[":
            return self._array(refs)
        if text == b"<<":
            return self._dict(refs)
        return LITERALS[text] if text in LITERALS else Operator(text.decode("latin-1"))

    def _ref(self, number: int) -> int | Ref:
        """*number* as a :class:`Ref` when ``G R`` follows it, else the number itself."""
        saved = self.pos
        second, third = self.token(), self.token()
        if second and second[0] == "num" and b"." not in second[1] and third == ("word", b"R"):
            return Ref(number)
        self.pos = saved
        return number

    def _array(self, refs: bool) -> list[Any]:
        """The items up to ``]``."""
        items = []
        while (token := self.token()) is not None and token[1] != b"]":
            items.append(self.value(token, refs))
        return items

    def _dict(self, refs: bool) -> dict[str, Any]:
        """The name-keyed entries up to ``>>``."""
        out: dict[str, Any] = {}
        while (token := self.token()) is not None and token[1] != b">>":
            key, token = self.value(token, refs), self.token()
            if token is None or token[1] == b">>":
                break
            value = self.value(token, refs)
            if isinstance(key, Name):
                out[key] = value
        return out


def _stream_raw(data: bytes, info: dict[str, Any], pos: int) -> tuple[bytes, int] | None:
    """The stream bytes after the dictionary ending at *pos*, and where the object ends."""
    match = STREAM_RE.match(data, pos)
    if match is None:
        return None
    start, length = match.end(), info.get("Length")
    if isinstance(length, int) and ENDSTREAM_RE.match(data, start + length):
        return data[start:start + length], start + length
    end = data.find(b"endstream", start)
    end = len(data) if end < 0 else end
    return data[start:end], end


def _objects(data: bytes) -> dict[int, Any]:
    """Every ``N G obj`` found by scanning, later definitions winning, so the xref table is not needed."""
    objects: dict[int, Any] = {}
    floor = 0
    for match in OBJECT_RE.finditer(data):
        if match.start() < floor:
            continue
        lexer = _Lexer(data, match.end())
        try:
            token = lexer.token()
            value = lexer.value(token, refs=True) if token is not None else None
        except (ValueError, IndexError, RecursionError):
            continue
        if isinstance(value, dict) and (stream := _stream_raw(data, value, lexer.pos)) is not None:
            value, floor = Stream(value, stream[0]), stream[1]
        objects[int(match.group(1))] = value
    _expand_object_streams(objects)
    return objects


def _expand_object_streams(objects: dict[int, Any]) -> None:
    """Add the objects packed in ``/ObjStm`` streams (PDF 1.5) that were not found directly."""
    for value in list(objects.values()):
        if not (isinstance(value, Stream) and value.info.get("Type") == "ObjStm"):
            continue
        data = _decode(value)
        first, count = value.info.get("First", 0), value.info.get("N", 0)
        lexer = _Lexer(data)
        header = [lexer.value(token) for _ in range(2 * count) if (token := lexer.token()) is not None]
        for number, offset in zip(header[::2], header[1::2], strict=False):
            if not (isinstance(number, int) and isinstance(offset, int)) or number in objects:
                continue
            inner = _Lexer(data, first + offset)
            token = inner.token()
            if token is not None:
                objects[number] = inner.value(token, refs=True)


def _decode(stream: Stream) -> bytes:
    """The stream's bytes with ``/FlateDecode`` undone; empty for other filters."""
    filters = stream.info.get("Filter", [])
    data = stream.raw
    for name in filters if isinstance(filters, list) else [filters]:
        if name not in FLATE:
            return b""
        inflater = zlib.decompressobj()
        try:
            data = inflater.decompress(data) + inflater.flush()
        except zlib.error:
            return b""
    return data


def _resolve(objects: dict[int, Any], value: Any) -> Any:
    """Follow indirect references to the object they name."""
    for _ in range(PDF_MAX_DEPTH):
        if not isinstance(value, Ref):
            return value
        value = objects.get(value.number)
    return None


def _collect(objects: dict[int, Any], node: Any, pages: list[dict[str, Any]], seen: set[int]) -> None:
    """Append the leaves of the page tree under *node* in order."""
    if isinstance(node, Ref):
        if node.number in seen:
            return
        seen.add(node.number)
    node = _resolve(objects, node)
    if not isinstance(node, dict):
        return
    if node.get("Type") == "Page" or "Kids" not in node:
        pages.append(node)
        return
    for kid in _resolve(objects, node["Kids"]) or []:
        _collect(objects, kid, pages, seen)


def _pages(objects: dict[int, Any]) -> list[dict[str, Any]]:
    """Pages in document order from the catalog, else every ``/Type /Page`` by object number."""
    pages: list[dict[str, Any]] = []
    catalogs = [v for v in objects.values() if isinstance(v, dict) and v.get("Type") == "Catalog"]
    if catalogs:
        _collect(objects, catalogs[-1].get("Pages"), pages, set())
    pages = [page for page in pages if page.get("Type") == "Page" or "Contents" in page]
    if not pages:
        pages = [v for _, v in sorted(objects.items()) if isinstance(v, dict) and v.get("Type") == "Page"]
    return pages


def _inherited(objects: dict[int, Any], page: dict[str, Any], key: str) -> Any:
    """*key* from the page or the nearest ancestor that has it."""
    node: Any = page
    for _ in range(PDF_MAX_DEPTH):
        if not isinstance(node, dict):
            return None
        if key in node:
            return _resolve(objects, node[key])
        node = _resolve(objects, node.get("Parent"))
    return None


def _operations(content: bytes) -> Iterator[tuple[str, list[Any]]]:
    """``(operator, operands)`` pairs of a content stream, inline images skipped."""
    lexer = _Lexer(content)
    operands: list[Any] = []
    while (token := lexer.token()) is not None:
        value = lexer.value(token)
        if not isinstance(value, Operator):
            operands.append(value)
            continue
        if value == "BI":
            end = INLINE_IMAGE_END_RE.search(content, lexer.pos)
            lexer.pos = end.end() if end else len(content)
        else:
            yield str(value), operands
        operands = []


def _numbers(operands: list[Any], count: int) -> list[float]:
    """The last *count* operands as floats; raises ValueError when there are too few."""
    values = operands[-count:] if count else []
    if len(values) < count or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        raise ValueError("operand underflow")
    return [float(v) for v in values]


def _content(objects: dict[int, Any], page: dict[str, Any]) -> bytes:
    """The page's content streams, decoded and joined."""
    contents = _resolve(objects, page.get("Contents"))
    parts = contents if isinstance(contents, list) else [contents]
    streams = [_resolve(objects, part) for part in parts]
    return b"\n".join(_decode(stream) for stream in streams if isinstance(stream, Stream))


def _media_box(objects: dict[int, Any], page: dict[str, Any]) -> tuple[float, float, float, float]:
    """The page's ``MediaBox`` as ``(x0, y0, x1, y1)``, letter size when missing."""
    box = _inherited(objects, page, "MediaBox")
    try:
        x0, y0, x1, y1 = (float(_resolve(objects, v)) for v in box)
    except (TypeError, ValueError):
        return DEFAULT_MEDIABOX
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)
