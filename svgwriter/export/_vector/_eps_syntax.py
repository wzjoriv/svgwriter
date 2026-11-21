"""
PostScript objects and tokenizer: names, strings, procedures, inline data and the DSC header.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ...model.transform.matrix import Matrix
from ._constants import (
    BOUNDS_RE,
    DOS_EPS_HEADER,
    DOS_EPS_MAGIC,
    ESCAPE_RE,
    HEX_DIGITS_RE,
    HEX_END,
    IMAGE_OPERATORS,
    INLINE_LOOKBACK,
    PS_HEADER,
    PS_TOKEN_RE,
    SIMPLE_ESCAPES,
)
from ._reading import string_end

__all__ = ["Inline", "Literal", "Mark", "Name", "Procedure"]


class Name(str):
    """An executable PostScript name such as ``moveto``."""


class Literal(str):
    """A literal PostScript name such as ``/box``, without the slash."""


class Procedure(list):
    """A procedure body ``{ ... }``, executed when its name is called or by ``exec``."""


class Mark:
    """The ``[`` mark that ``]`` collects an array up to."""


class Inline(bytes):
    """Hex-decoded image data that follows an image operator reading ``currentfile``."""


class _File:
    """The ``currentfile`` object, whose data is the program's :class:`Inline` bytes."""


@dataclass
class _Font:
    """A font from ``findfont``: its name and the matrix ``scalefont``/``makefont`` built."""

    name: str
    matrix: Matrix


class _Underflow(Exception):
    """An operator found too few operands, or operands of the wrong type."""


def _unescape(raw: bytes) -> bytes:
    """The bytes of a PostScript string body, backslash escapes resolved."""
    def replace(match: re.Match[bytes]) -> bytes:
        code = match.group(1)
        if code[:1].isdigit():
            return bytes([int(code, 8) & 0xFF])
        if code in (b"\r\n", b"\n", b"\r"):
            return b""
        return SIMPLE_ESCAPES.get(code, code)
    return ESCAPE_RE.sub(replace, raw)


def _inline_hex(data: bytes, pos: int) -> tuple[Inline, int]:
    """The ASCII-hex data from *pos* up to its ``>``, and the position after it."""
    end = data.find(HEX_END, pos)
    end = len(data) if end < 0 else end
    digits = HEX_DIGITS_RE.sub(b"", data[pos:end])
    return Inline(bytes.fromhex(digits[:len(digits) // 2 * 2].decode("ascii"))), end + 1


def _parse(data: bytes) -> Procedure:
    """The program's objects, procedures nested; unbalanced braces are tolerated."""
    stack = [Procedure()]
    pos = 0
    while (match := PS_TOKEN_RE.match(data, pos)) is not None:
        pos, kind, text = match.end(), match.lastgroup, match.group()
        if kind == "string":
            pos = string_end(data, pos)
            stack[-1].append(_unescape(data[match.end():pos - 1]))
        elif kind == "name" and len(stack) == 1 and text in IMAGE_OPERATORS and any(
                item == "currentfile" for item in stack[0][-INLINE_LOOKBACK:] if isinstance(item, Name)):
            inline, pos = _inline_hex(data, pos)
            stack[0] += [inline, Name(text.decode("latin-1"))]
        elif kind == "num":
            stack[-1].append(float(text))
        elif kind == "radix":
            base, digits = text.split(b"#")
            stack[-1].append(float(int(digits, int(base))) if 2 <= int(base) <= 36 else 0.0)
        elif kind == "literal":
            stack[-1].append(Literal(text[1:].decode("latin-1")))
        elif kind in ("name", "dict"):
            stack[-1].append(Name(text.decode("latin-1")))
        elif kind == "open":
            stack.append(Procedure())
        elif kind == "close" and len(stack) > 1:
            procedure = stack.pop()
            stack[-1].append(procedure)
        elif kind == "hex":
            digits = HEX_DIGITS_RE.sub(b"", text)
            stack[-1].append(bytes.fromhex(digits[:len(digits) // 2 * 2].decode("ascii")))
        elif kind == "a85":
            stack[-1].append(b"")
    while len(stack) > 1:
        procedure = stack.pop()
        stack[-1].append(procedure)
    return stack[0]


def _bounding_box(data: bytes) -> tuple[float, float, float, float] | None:
    """``%%HiResBoundingBox`` or ``%%BoundingBox`` as ``(llx, lly, urx, ury)``."""
    for pattern in BOUNDS_RE.values():
        match = pattern.search(data)
        if match is not None:
            try:
                llx, lly, urx, ury = (float(v) for v in match.groups())
            except ValueError:
                continue
            if urx > llx and ury > lly:
                return llx, lly, urx, ury
    return None


def _postscript(data: bytes) -> bytes:
    """The PostScript section of *data*, unwrapping a DOS EPS binary header."""
    if data[:4] == DOS_EPS_MAGIC and len(data) >= DOS_EPS_HEADER.size:
        _, offset, length = DOS_EPS_HEADER.unpack_from(data)
        data = data[offset:offset + length]
    if not data.lstrip().startswith(PS_HEADER):
        raise ValueError("not PostScript: missing the '%!' header")
    return data
