"""
Reading the vector paths of a PDF page back into a document.
"""

from __future__ import annotations

import math
import re
import zlib
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Final

from ...transform.matrix import Matrix
from ._constants import (
    BLACK,
    CAP_NAMES,
    DEFAULT_MEDIABOX,
    ENCRYPT_RE,
    ENDSTREAM_RE,
    FLATE,
    HAIRLINE,
    HEADER_WINDOW,
    INLINE_IMAGE_END_RE,
    JOIN_NAMES,
    LITERALS,
    NAME_ESCAPE_RE,
    OBJECT_RE,
    PAINTS,
    PDF_HEADER,
    PDF_MAX_DEPTH,
    PDF_TOKEN_RE,
    STREAM_RE,
)
from ._reading import Outline, Shape, cmyk_to_rgb, string_end, to_document

if TYPE_CHECKING:
    from ...document import Document
    from ._reading import RGB, Op

__all__ = ["read_pdf"]


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


@dataclass
class _State:
    """The PDF graphics state the reader tracks."""

    ctm: Matrix
    fill: RGB = BLACK
    stroke: RGB = BLACK
    fill_alpha: float = 1.0
    stroke_alpha: float = 1.0
    group_alpha: float = 1.0
    line_width: float = 1.0
    cap: int = 0
    join: int = 0
    miter: float = 4.0
    dashes: tuple[float, ...] = ()
    clip: list[Op] | None = None
    fill_pattern: Any = None


class _Painter:
    """Runs content streams, collecting painted shapes."""

    def __init__(self, objects: dict[int, Any], ctm: Matrix) -> None:
        self.objects = objects
        self.state = _State(ctm)
        self.saved: list[_State] = []
        self.outline = Outline()
        self.shapes: list[Any] = []
        self.depth = 0
        self.pending_clip: bool | None = None
        self.text_matrix = self.line_matrix = Matrix()
        self.leading = 0.0
        self.base = ctm
        self.page: list[Op] = []

    def run(self, content: bytes, resources: dict[str, Any]) -> None:
        """Execute *content* with *resources*; malformed operations are skipped."""
        for op, operands in _operations(content):
            handler = _HANDLERS.get(op)
            if handler is None:
                continue
            try:
                handler(self, operands, resources)
            except (ValueError, TypeError, IndexError, KeyError, ZeroDivisionError):
                continue

    def resource(self, resources: dict[str, Any], category: str, name: Any) -> Any:
        """The named entry of a resource category such as ``/ExtGState``."""
        table = _resolve(self.objects, resources.get(category)) or {}
        return _resolve(self.objects, table.get(name)) if isinstance(table, dict) else None

    def take(self) -> list[Op]:
        """The current path, ending it; a pending ``W``/``W*`` makes it (part of) the clip first."""
        ops = self.outline.take()
        if self.pending_clip is not None and ops:
            self.state.clip = _intersect(self.state.clip, ops)
        self.pending_clip = None
        return ops

    def paint(self, fill: bool, stroke: bool, evenodd: bool) -> None:
        """Paint the current path and start a new one."""
        state, ops = self.state, self.take()
        if fill and state.fill_pattern is not None and ops and fill_with_pattern(self, ops, evenodd, stroke):
            return
        scale = math.sqrt(abs(state.ctm.determinant))
        self.shapes.append(Shape(
            ops, fill=state.fill if fill else None, stroke=state.stroke if stroke else None,
            fill_opacity=state.fill_alpha * state.group_alpha, stroke_opacity=state.stroke_alpha * state.group_alpha,
            evenodd=evenodd, stroke_width=state.line_width * scale if state.line_width > 0 else HAIRLINE,
            linecap=CAP_NAMES[state.cap % len(CAP_NAMES)], linejoin=JOIN_NAMES[state.join % len(JOIN_NAMES)],
            miter_limit=state.miter, dashes=tuple(d * scale for d in state.dashes), clip=state.clip))

    def form(self, xobject: Any, resources: dict[str, Any]) -> None:
        """Draw a Form XObject; a transparency group takes the current fill alpha as its opacity."""
        if isinstance(xobject, Stream) and xobject.info.get("Subtype") == "Image":
            draw_image(self, xobject)
            return
        if not (isinstance(xobject, Stream) and xobject.info.get("Subtype") == "Form") or self.depth >= PDF_MAX_DEPTH:
            return
        saved = self.state
        matrix = _resolve(self.objects, xobject.info.get("Matrix")) or [1, 0, 0, 1, 0, 0]
        self.state = replace(saved, ctm=saved.ctm @ Matrix(*map(float, matrix)))
        if "Group" in xobject.info:
            self.state = replace(self.state, group_alpha=saved.group_alpha * saved.fill_alpha,
                                 fill_alpha=1.0, stroke_alpha=1.0)
        inner = _resolve(self.objects, xobject.info.get("Resources"))
        self.depth += 1
        try:
            self.run(_decode(xobject), inner if isinstance(inner, dict) else resources)
        finally:
            self.depth -= 1
            self.state = saved


def _set_dash(state: _State, value: Any) -> None:
    """Set the dash array from ``[array phase]`` or a bare array; the phase is dropped."""
    pattern = value[0] if isinstance(value, list) and value and isinstance(value[0], list) else value
    state.dashes = tuple(float(v) for v in pattern) if isinstance(pattern, list) else ()


def _ext_gstate(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    """``gs``: alpha constants and line parameters from an ``/ExtGState`` dictionary."""
    entry = painter.resource(resources, "ExtGState", operands[-1])
    if not isinstance(entry, dict):
        return
    state = painter.state
    fields = {"CA": "stroke_alpha", "ca": "fill_alpha", "LW": "line_width", "ML": "miter"}
    for key, attribute in fields.items():
        if isinstance(entry.get(key), (int, float)):
            setattr(state, attribute, float(entry[key]))
    for key, attribute in (("LC", "cap"), ("LJ", "join")):
        if isinstance(entry.get(key), int):
            setattr(state, attribute, entry[key])
    if "D" in entry:
        _set_dash(state, _resolve(painter.objects, entry["D"]))


def _color(operands: list[Any]) -> RGB:
    """An RGB colour from 1 (gray), 3 (RGB) or 4 (CMYK) numeric operands, as in DeviceGray/RGB/CMYK."""
    values = [float(v) for v in operands if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if len(values) == 1:
        return (values[0],) * 3
    if len(values) == 3:
        return (values[0], values[1], values[2])
    if len(values) == 4:
        return cmyk_to_rgb(*values)
    raise ValueError("unsupported colour operands")


def _set_color(attribute: str, count: int | None) -> Callable[[_Painter, list[Any], dict[str, Any]], None]:
    """A handler setting the fill or stroke colour from *count* operands (any count when None)."""
    def handler(painter: _Painter, operands: list[Any], _: dict[str, Any]) -> None:
        setattr(painter.state, attribute, _color(operands[-count:] if count else operands))
    return handler


def _fill_paint(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    """``scn``: a pattern name selects a pattern fill; numbers set a plain colour and clear the pattern."""
    if operands and isinstance(operands[-1], Name):
        painter.state.fill_pattern = painter.resource(resources, "Pattern", operands[-1])
        return
    painter.state.fill_pattern = None
    painter.state.fill = _color(operands)


def _paint(op: str) -> Callable[[_Painter, list[Any], dict[str, Any]], None]:
    """A handler for a path-painting operator such as ``f*`` or ``b``."""
    fill, stroke, evenodd, close = PAINTS[op]

    def handler(painter: _Painter, _: list[Any], __: dict[str, Any]) -> None:
        if close:
            painter.outline.close()
        painter.paint(fill, stroke, evenodd)
    return handler


def _restore(painter: _Painter) -> None:
    """``Q``: restore the saved graphics state, if any."""
    if painter.saved:
        painter.state = painter.saved.pop()


def _setter(attribute: str, convert: Callable[[float], Any]) -> Callable[[_Painter, list[Any], dict[str, Any]], None]:
    """A handler storing one number, converted, in a graphics-state field."""
    def handler(painter: _Painter, operands: list[Any], _: dict[str, Any]) -> None:
        setattr(painter.state, attribute, convert(_numbers(operands, 1)[0]))
    return handler


from ._pdf_content import CONTENT_HANDLERS, draw_image  # noqa: E402
from ._pdf_paint import fill_with_pattern, paint_shading  # noqa: E402

_HANDLERS: Final[dict[str, Callable[[_Painter, list[Any], dict[str, Any]], None]]] = {
    "m": lambda p, o, _: p.outline.move(p.state.ctm, *_numbers(o, 2)),
    "l": lambda p, o, _: p.outline.line(p.state.ctm, *_numbers(o, 2)),
    "c": lambda p, o, _: p.outline.curve(p.state.ctm, *_numbers(o, 6)),
    "v": lambda p, o, _: p.outline.curve(p.state.ctm, *(p.outline.user_current(p.state.ctm) or ()), *_numbers(o, 4)),
    "y": lambda p, o, _: p.outline.curve(p.state.ctm, *_numbers(o, 4), *_numbers(o, 2)),
    "h": lambda p, o, _: p.outline.close(),
    "re": lambda p, o, _: p.outline.rect(p.state.ctm, *_numbers(o, 4)),
    "n": lambda p, o, _: p.take(),
    **{op: _paint(op) for op in PAINTS},
    "q": lambda p, o, _: p.saved.append(replace(p.state)),
    "Q": lambda p, o, _: _restore(p),
    "cm": lambda p, o, _: setattr(p.state, "ctm", p.state.ctm @ Matrix(*_numbers(o, 6))),
    "w": _setter("line_width", float),
    "J": _setter("cap", int),
    "j": _setter("join", int),
    "M": _setter("miter", float),
    "d": lambda p, o, _: _set_dash(p.state, o[0] if o else []),
    "gs": _ext_gstate,
    "rg": _set_color("fill", 3), "RG": _set_color("stroke", 3),
    "g": _set_color("fill", 1), "G": _set_color("stroke", 1),
    "k": _set_color("fill", 4), "K": _set_color("stroke", 4),
    "sc": _set_color("fill", None), "scn": lambda p, o, r: _fill_paint(p, o, r),
    "sh": lambda p, o, r: paint_shading(p, o, r),
    "SC": _set_color("stroke", None), "SCN": _set_color("stroke", None),
    "cs": lambda p, o, _: setattr(p.state, "fill", BLACK),
    "CS": lambda p, o, _: setattr(p.state, "stroke", BLACK),
    "Do": lambda p, o, r: p.form(p.resource(r, "XObject", o[-1]), r),
}


_HANDLERS.update(CONTENT_HANDLERS)


def _intersect(current: list[Op] | None, ops: list[Op]) -> list[Op]:
    """The clip after intersecting *current* with the outline *ops* (both page-space operations)."""
    if current is None:
        return ops
    from ...ops.boolean import intersection
    from ._reading import _path

    return _operations_of(intersection(_path(Shape(current)).d, _path(Shape(ops)).d))


def _operations_of(data: Any) -> list[Op]:
    """Path data as ``M``/``L``/``C``/``Z`` operations."""
    from ...ops._skia import from_skia, to_skia
    from ...pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo

    ops: list[Op] = []
    here = (0.0, 0.0)
    for command in from_skia(to_skia(data)):
        if isinstance(command, MoveTo):
            here = (command.x, command.y)
            ops.append(("M", here))
        elif isinstance(command, LineTo):
            here = (command.x, command.y)
            ops.append(("L", here))
        elif isinstance(command, QuadTo):
            q, end = (command.x1, command.y1), (command.x, command.y)
            ops.append(("C", (here[0] + 2 / 3 * (q[0] - here[0]), here[1] + 2 / 3 * (q[1] - here[1]),
                              end[0] + 2 / 3 * (q[0] - end[0]), end[1] + 2 / 3 * (q[1] - end[1]), *end)))
            here = end
        elif isinstance(command, CurveTo):
            here = (command.x, command.y)
            ops.append(("C", (command.x1, command.y1, command.x2, command.y2, *here)))
        elif isinstance(command, ClosePath):
            ops.append(("Z", ()))
    return ops


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


def read_pdf(data: bytes, *, page: int = 0) -> Document:
    """Read the vector paths of one PDF page as filled and stroked ``<path>`` elements.

    Parameters
    ----------
    data : bytes
        The PDF file.
    page : int, optional
        Zero-based index of the page to read. Defaults to 0.

    Returns
    -------
    Document
        A document the size of the page's ``MediaBox`` in points, y pointing down.

    Raises
    ------
    ValueError
        If *data* is not a PDF, is encrypted, has no pages, or has no page *page*.

    See Also
    --------
    svgwriter.export._vector._eps_read.read_eps : Read PostScript.

    Notes
    -----
    Objects are found by scanning for ``N G obj``, so a broken cross-reference
    table does not matter; object streams are unpacked. Supported: content
    streams that are uncompressed or ``/FlateDecode`` (other filters are
    skipped), Form XObjects drawn with ``Do`` (transparency groups take the
    current fill alpha), the path operators ``m l c v y h re`` and
    ``S s f F f* B B* b b* n``, the state operators ``q Q cm w J j M d`` and
    ``gs`` (``CA``, ``ca``, ``LW``, ``LC``, ``LJ``, ``ML``, ``D``), and the
    colour operators ``rg RG g G k K`` plus ``cs``/``sc``/``scn`` read by
    operand count as gray, RGB or CMYK. Images (JPEG, or Flate-compressed
    gray/RGB/CMYK samples with soft masks) become ``<image>`` elements,
    clipping paths (``W``, ``W*``) become ``clip-path``, and text
    (``BT``..``ET`` with ``Tf``, ``Td``, ``TD``, ``Tm``, ``T*``, ``Tj``,
    ``TJ``, ``'``, ``"``) becomes ``<text>`` in the font family named by the
    font, decoded as single-byte text. Axial and radial shadings (``sh`` and
    shading patterns) become linear and radial gradients, and tiling
    patterns become ``<pattern>`` elements. Blend modes, mesh shadings and
    ``/Rotate`` are ignored.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._vector._pdf_read import read_pdf
    >>> doc = svg.Document(20, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> back = read_pdf(svg.export.export(doc, "pdf"))
    >>> back.root.get("width"), back[0].get("fill")
    (20.0, '#ff0000')
    """
    if PDF_HEADER not in data[:HEADER_WINDOW]:
        raise ValueError("not a PDF file: no '%PDF-' header")
    if ENCRYPT_RE.search(data):
        raise ValueError("encrypted PDF files are not supported")
    objects = _objects(data)
    pages = _pages(objects)
    if not pages:
        raise ValueError("no pages found in the PDF file")
    if not 0 <= page < len(pages):
        raise ValueError(f"page {page} out of range: the PDF file has {len(pages)} page(s)")
    leaf = pages[page]
    x0, y0, x1, y1 = _media_box(objects, leaf)
    painter = _Painter(objects, Matrix(1.0, 0.0, 0.0, -1.0, -x0, y1))
    width, height = x1 - x0, y1 - y0
    painter.page = [("M", (0.0, 0.0)), ("L", (width, 0.0)), ("L", (width, height)), ("L", (0.0, height)), ("Z", ())]
    resources = _inherited(objects, leaf, "Resources")
    painter.run(_content(objects, leaf), resources if isinstance(resources, dict) else {})
    return to_document(painter.shapes, (0.0, 0.0, x1 - x0, y1 - y0))
