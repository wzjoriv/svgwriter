"""
Reading EPS and PostScript drawings back into a document with a small stack machine.
"""

from __future__ import annotations

import math
import re
import struct
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Final

import numpy as np

from ...transform.matrix import Matrix
from ._pdf_content import _STYLE_RE, DEFAULT_TEXT_SIZE, _clip
from ._pdf_read import _intersect
from ._reading import BLACK, HAIRLINE, Outline, Shape, _hex, cmyk_to_rgb, string_end, to_document

if TYPE_CHECKING:
    from ...document import Document
    from ._reading import RGB

__all__ = ["read_eps"]

PS_HEADER: Final = b"%!"
DOS_EPS_MAGIC: Final = b"\xc5\xd0\xd3\xc6"
DOS_EPS_HEADER: Final = struct.Struct("<4sII")
MAX_DEPTH: Final = 64
MAX_STEPS: Final = 2_000_000
SAVE_OBJECT: Final = object()
CAPS: Final = ("butt", "round", "square")
JOINS: Final = ("miter", "round", "bevel")
CHANNEL_MAX: Final = 255.0
GRAY_CHANNELS: Final = 1
RGB_CHANNELS: Final = 3
CMYK_CHANNELS: Final = 4
SUPPORTED_BITS: Final = 8
MAX_IMAGE_CALLS: Final = 100_000
IMAGE_OPERATORS: Final = (b"image", b"colorimage")
INLINE_LOOKBACK: Final = 8
HEX_END: Final = b">"
DEFAULT_FONT: Final = "serif"
_HEX_DIGITS_RE: Final = re.compile(rb"[^0-9A-Fa-f]")
_ESCAPE_RE: Final = re.compile(rb"\\([0-7]{1,3}|\r\n|\n|\r|.)", re.S)
_SIMPLE_ESCAPES: Final = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f"}
_DELIMITERS: Final = rb"\x00\t\n\x0c\r ()<>\[\]{}/%"
_TOKEN_RE: Final = re.compile(
    rb"(?P<skip>[\x00\t\n\x0c\r ]+|%[^\r\n]*)"
    rb"|(?P<radix>\d+#[0-9A-Za-z]+)(?![^" + _DELIMITERS + rb"])"
    rb"|(?P<num>[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)(?![^" + _DELIMITERS + rb"])"
    rb"|(?P<literal>/[^" + _DELIMITERS + rb"]*)"
    rb"|(?P<string>\()"
    rb"|(?P<a85><~.*?~>)"
    rb"|(?P<dict><<|>>)"
    rb"|(?P<hex><[^<>]*>)"
    rb"|(?P<open>\{)|(?P<close>\})"
    rb"|(?P<name>[\[\]]|[^" + _DELIMITERS + rb"]+)"
    rb"|(?P<other>.)", re.S)
_BOUNDS_RE: Final = {name: re.compile(rb"^%%" + name + rb":\s*([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)",
                                      re.M) for name in (b"HiResBoundingBox", b"BoundingBox")}


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
        return _SIMPLE_ESCAPES.get(code, code)
    return _ESCAPE_RE.sub(replace, raw)


def _inline_hex(data: bytes, pos: int) -> tuple[Inline, int]:
    """The ASCII-hex data from *pos* up to its ``>``, and the position after it."""
    end = data.find(HEX_END, pos)
    end = len(data) if end < 0 else end
    digits = _HEX_DIGITS_RE.sub(b"", data[pos:end])
    return Inline(bytes.fromhex(digits[:len(digits) // 2 * 2].decode("ascii"))), end + 1


def _parse(data: bytes) -> Procedure:
    """The program's objects, procedures nested; unbalanced braces are tolerated."""
    stack = [Procedure()]
    pos = 0
    while (match := _TOKEN_RE.match(data, pos)) is not None:
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
            digits = _HEX_DIGITS_RE.sub(b"", text)
            stack[-1].append(bytes.fromhex(digits[:len(digits) // 2 * 2].decode("ascii")))
        elif kind == "a85":
            stack[-1].append(b"")
    while len(stack) > 1:
        procedure = stack.pop()
        stack[-1].append(procedure)
    return stack[0]


@dataclass
class _State:
    """The PostScript graphics state the reader tracks; one colour serves fill and stroke."""

    ctm: Matrix
    color: RGB = BLACK
    line_width: float = 1.0
    cap: int = 0
    join: int = 0
    miter: float = 10.0
    dashes: tuple[float, ...] = ()
    font: _Font | None = None
    clip: list[tuple[str, tuple[float, ...]]] | None = None


class _Machine:
    """Executes a parsed program, collecting painted shapes."""

    def __init__(self, ctm: Matrix) -> None:
        self.stack: list[Any] = []
        self.dicts: list[dict[str, Any]] = [{}]
        self.state = _State(ctm)
        self.saved: list[tuple[_State, Outline]] = []
        self.outline = Outline()
        self.shapes: list[Any] = []
        self.file_data = b""
        self.steps = 0
        self.done = False

    def execute(self, program: list[Any], depth: int = 0) -> None:
        """Push literals and call names in *program*; stops at ``showpage`` or the step limit."""
        for item in program:
            if self.done or self.steps >= MAX_STEPS:
                return
            self.steps += 1
            if isinstance(item, Name):
                self.call(item, depth)
            elif isinstance(item, Inline):
                self.file_data = bytes(item)
            else:
                self.stack.append(item)

    def call(self, name: str, depth: int) -> None:
        """Run a user definition or a built-in operator; unknown names are ignored."""
        found, value = self.lookup(name)
        if found:
            if isinstance(value, (Procedure, Name)) and depth < MAX_DEPTH:
                self.execute(value if isinstance(value, Procedure) else [value], depth + 1)
            elif not isinstance(value, (Procedure, Name)):
                self.stack.append(value)
            return
        operator = OPERATORS.get(name)
        if operator is None:
            return
        try:
            operator(self, depth)
        except (_Underflow, ValueError, ZeroDivisionError, OverflowError, TypeError, AttributeError):
            return

    def lookup(self, name: str) -> tuple[bool, Any]:
        """Whether *name* is defined on the dictionary stack, and its value from the innermost definition."""
        for names in reversed(self.dicts):
            if name in names:
                return True, names[name]
        return False, None

    def pop(self, count: int = 1, kind: type | tuple[type, ...] = float) -> list[Any]:
        """The top *count* operands; on too few or a wrong type they are dropped and the operator skipped."""
        values = self.stack[-count:] if count <= len(self.stack) else None
        del self.stack[-count:]
        if values is None or not all(isinstance(v, kind) for v in values):
            raise _Underflow
        return values

    def paint(self, fill: bool, evenodd: bool = False, ops: list | None = None) -> None:
        """Paint *ops* (the current path, consumed, when None) with the current colour."""
        state = self.state
        ops = self.outline.take() if ops is None else ops
        scale = math.sqrt(abs(state.ctm.determinant))
        self.shapes.append(Shape(
            ops, fill=state.color if fill else None, stroke=None if fill else state.color, evenodd=evenodd,
            stroke_width=state.line_width * scale if state.line_width > 0 else HAIRLINE, linecap=CAPS[state.cap % len(CAPS)],
            linejoin=JOINS[state.join % len(JOINS)], miter_limit=state.miter,
            dashes=tuple(d * scale for d in state.dashes), clip=state.clip))

    def relative(self, *offsets: float) -> list[float]:
        """Absolute user coordinates of *offsets* (x, y pairs) from the current point."""
        current = self.outline.user_current(self.state.ctm)
        if current is None:
            raise _Underflow
        return [v + current[i % 2] for i, v in enumerate(offsets)]

    def transform(self, matrix: Matrix) -> None:
        """Concatenate *matrix* to the current transform."""
        self.state.ctm = self.state.ctm @ matrix


def _arc(machine: _Machine, clockwise: bool) -> None:
    """``arc``/``arcn``: a circular arc about (x, y), joined to the current point by a line."""
    x, y, r, a1, a2 = machine.pop(5)
    start, end = math.radians(a1), math.radians(a2)
    sweep = (start - end) % (2 * math.pi) if clockwise else (end - start) % (2 * math.pi)
    if sweep == 0 and a1 != a2:
        sweep = 2 * math.pi
    machine.outline.arc(machine.state.ctm, (x, y), (r, r), start, -sweep if clockwise else sweep)


def _rectangle(machine: _Machine, fill: bool) -> None:
    """``rectfill``/``rectstroke``: paint a rectangle without touching the current path."""
    rect = Outline()
    rect.rect(machine.state.ctm, *machine.pop(4))
    machine.paint(fill, ops=rect.take())


def _def(machine: _Machine, _: int) -> None:
    """``def``: bind a literal name to a value in the innermost dictionary."""
    value = machine.pop(1, object)[0]
    machine.dicts[-1][machine.pop(1, Literal)[0]] = value


def _load(machine: _Machine, _: int) -> None:
    """``load``: push a name's value, or the executable name of a built-in operator."""
    name = machine.pop(1, Literal)[0]
    found, value = machine.lookup(name)
    machine.stack.append(value if found else Name(name))


def _exec(machine: _Machine, depth: int) -> None:
    """``exec``: run a procedure or executable name from the stack."""
    value = machine.pop(1, object)[0]
    if isinstance(value, Procedure) and depth < MAX_DEPTH:
        machine.execute(value, depth + 1)
    elif isinstance(value, Name):
        machine.call(value, depth + 1)


def _to_mark(machine: _Machine) -> list[Any]:
    """Pop the operands above the topmost mark, and the mark."""
    marks = [i for i, v in enumerate(machine.stack) if isinstance(v, Mark)]
    if not marks:
        raise _Underflow
    items = machine.stack[marks[-1] + 1:]
    del machine.stack[marks[-1]:]
    return items


def _close_dict(machine: _Machine, _: int) -> None:
    """``>>``: a dictionary from the key-value pairs above the mark."""
    items = _to_mark(machine)
    machine.stack.append({k: v for k, v in zip(items[::2], items[1::2], strict=False) if isinstance(k, Literal)})


def _begin(machine: _Machine, _: int) -> None:
    """``begin``: push a dictionary onto the dictionary stack."""
    machine.dicts.append(machine.pop(1, dict)[0])


def _end(machine: _Machine, _: int) -> None:
    """``end``: pop the dictionary stack, never the outermost dictionary."""
    if len(machine.dicts) > 1:
        machine.dicts.pop()


def _setdash(machine: _Machine, _: int) -> None:
    """``setdash``: the dash array; the offset is dropped."""
    machine.pop(1)
    pattern = machine.pop(1, list)[0]
    machine.state.dashes = tuple(float(v) for v in pattern if isinstance(v, float))


def _grestore(machine: _Machine, _: int) -> None:
    """``grestore``: restore the saved state and path, if any."""
    if machine.saved:
        machine.state, machine.outline = machine.saved.pop()


def _gsave(machine: _Machine, _: int) -> None:
    """Save the graphics state, current path included."""
    machine.saved.append((replace(machine.state), machine.outline.copy()))


def _setter(attribute: str, convert: Callable[[float], Any]) -> Callable[[_Machine, int], None]:
    """An operator storing one number, converted, in a graphics-state field."""
    def operator(machine: _Machine, _: int) -> None:
        setattr(machine.state, attribute, convert(machine.pop(1)[0]))
    return operator


def _rotation(degrees: float) -> Matrix:
    """A rotation by *degrees* counter-clockwise in PostScript's y-up space."""
    cos, sin = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return Matrix(cos, sin, -sin, cos, 0.0, 0.0)


def _binary(function: Callable[[float, float], float]) -> Callable[[_Machine, int], None]:
    """An arithmetic operator applying *function* to the top two numbers."""
    def operator(machine: _Machine, _: int) -> None:
        a, b = machine.pop(2)
        machine.stack.append(float(function(a, b)))
    return operator


def _clip_to_path(machine: _Machine, _: int) -> None:
    """``clip``/``eoclip``: intersect the clip with the current path, which stays the current path."""
    ops = list(machine.outline.ops)
    if ops:
        machine.state.clip = _intersect(machine.state.clip, ops)


def _source_bytes(machine: _Machine, source: Any, need: int, depth: int) -> bytes:
    """Up to *need* bytes from an image data source: ``currentfile``, a string or a procedure returning strings."""
    if isinstance(source, _File):
        return machine.file_data[:need]
    if isinstance(source, bytes):
        return source[:need]
    if not isinstance(source, Procedure):
        return b""
    chunks: list[bytes] = []
    size = 0
    for _ in range(MAX_IMAGE_CALLS):
        before = len(machine.stack)
        machine.execute(source, depth + 1)
        if len(machine.stack) <= before or not isinstance(machine.stack[-1], bytes) or not machine.stack[-1]:
            break
        chunks.append(machine.stack.pop())
        size += len(chunks[-1])
        if size >= need:
            break
    return b"".join(chunks)[:need]


def _place_image(machine: _Machine, depth: int, operands: list[Any], sources: list[Any], channels: int) -> None:
    """Add an ``Image`` for 8-bit samples read from *sources* (one interleaved source, or one per channel)."""
    from ...elements.structure import Image

    width, height, bits, matrix = operands
    if int(bits) != SUPPORTED_BITS or not isinstance(matrix, list) or width < 1 or height < 1:
        raise _Underflow
    columns, rows = int(width), int(height)
    count = columns * rows
    if len(sources) == 1:
        data = _source_bytes(machine, sources[0], count * channels, depth)
        raw = np.frombuffer(data, np.uint8)
    else:
        planes = [np.frombuffer(_source_bytes(machine, s, count, depth), np.uint8) for s in sources]
        raw = np.dstack(planes).ravel() if len({p.size for p in planes}) == 1 else np.empty(0, np.uint8)
    if raw.size < count * channels:
        raise _Underflow
    samples = raw[:count * channels].reshape(rows, columns, channels).astype(np.float32) / CHANNEL_MAX
    if channels == GRAY_CHANNELS:
        rgb = np.repeat(samples, RGB_CHANNELS, axis=2)
    elif channels == CMYK_CHANNELS:
        c, m, y, k = (samples[..., i] for i in range(CMYK_CHANNELS))
        rgb = np.dstack([(1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k)])
    else:
        rgb = samples
    pixels = np.concatenate([rgb, np.ones((rows, columns, 1), np.float32)], axis=2)
    image = Image(pixels, 0, 0, columns, rows, preserve_aspect_ratio="none")
    image.t = machine.state.ctm @ Matrix(*(float(v) for v in matrix[:6])).inverse()
    if machine.state.clip:
        _clip(image, machine.state.clip)
    machine.shapes.append(image)


def _image(machine: _Machine, depth: int) -> None:
    """``image`` in its five-operand gray form."""
    operands = machine.pop(5, object)
    _place_image(machine, depth, operands[:4], operands[4:], GRAY_CHANNELS)


def _colorimage(machine: _Machine, depth: int) -> None:
    """``colorimage``: gray, RGB or CMYK samples from one source or one source per component."""
    channels = int(machine.pop(1)[0])
    multi = machine.pop(1, bool)[0]
    if channels not in (GRAY_CHANNELS, RGB_CHANNELS, CMYK_CHANNELS):
        raise _Underflow
    sources = machine.pop(channels if multi else 1, object)
    _place_image(machine, depth, machine.pop(4, object), sources, channels)


def _filter(machine: _Machine, _: int) -> None:
    """``filter``: the ASCII-hex data is decoded when read, so the source is returned unchanged."""
    machine.pop(1, Literal)
    machine.pop(1, object)
    machine.stack.append(_File())


def _find_font(machine: _Machine, _: int) -> None:
    """``findfont``: a font of one unit size under the given name."""
    machine.stack.append(_Font(machine.pop(1, str)[0], Matrix()))


def _scale_font(machine: _Machine, _: int) -> None:
    """``scalefont``: scale the font matrix."""
    font, size = machine.pop(2, object)
    machine.stack.append(_Font(font.name, Matrix.scale(size) @ font.matrix))


def _make_font(machine: _Machine, _: int) -> None:
    """``makefont``: transform the font matrix by a six-element matrix."""
    font, matrix = machine.pop(2, object)
    machine.stack.append(_Font(font.name, Matrix(*(float(v) for v in matrix[:6])) @ font.matrix))


def _select_font(machine: _Machine, _: int) -> None:
    """``selectfont``: a name with a size or a matrix, made the current font."""
    name, scale = machine.pop(2, object)
    matrix = Matrix.scale(scale) if isinstance(scale, float) else Matrix(*(float(v) for v in scale[:6]))
    machine.state.font = _Font(str(name), matrix)


def _set_font(machine: _Machine, _: int) -> None:
    """``setfont``: make a font current."""
    machine.state.font = machine.pop(1, _Font)[0]


def _move_current(machine: _Machine, x: float, y: float) -> None:
    """Set the current point to user coordinates (*x*, *y*) without adding a path segment."""
    outline = machine.outline
    point = tuple(machine.state.ctm.apply(x, y))
    if outline.ops and outline.ops[-1][0] == "M":
        outline.ops[-1] = ("M", point)
        outline.start = point
    outline.current = point


def _run(machine: _Machine, text: str) -> tuple[float, float]:
    """Draw *text* at the current point; the user-space advance of its measured width."""
    from ...elements.text import Text
    from ...ops.text import text_width

    current = machine.outline.user_current(machine.state.ctm)
    font = machine.state.font
    if current is None or font is None:
        raise _Underflow
    a, b, c, d, _, _ = font.matrix.as_tuple()
    size = math.sqrt(abs(a * d - b * c)) or DEFAULT_TEXT_SIZE
    unit = Matrix(a / size, b / size, c / size, d / size, 0.0, 0.0)
    style = font.name.lower()
    family = _STYLE_RE.sub("", font.name) or DEFAULT_FONT
    bold, italic = "bold" in style, "italic" in style or "oblique" in style
    if text.strip():
        run = Text(text, x=0, y=0, font_size=size, font_family=family, fill=_hex(machine.state.color),
                   font_weight="bold" if bold else None, font_style="italic" if italic else None,
                   xml_space="preserve")
        run.t = machine.state.ctm @ Matrix.translate(*current) @ unit @ Matrix.scale(1, -1)
        if machine.state.clip:
            _clip(run, machine.state.clip)
        machine.shapes.append(run)
    width = text_width(text, family, size, weight="bold" if bold else "normal", italic=italic)
    return tuple(unit.apply(width, 0.0))


def _advance(machine: _Machine, dx: float, dy: float) -> None:
    """Move the current point by a user-space vector."""
    x, y = machine.outline.user_current(machine.state.ctm)
    _move_current(machine, x + dx, y + dy)


def _show_spaced(machine: _Machine, text: bytes, extras: list[tuple[float, float]]) -> None:
    """Show *text*, adding the user-space vector in *extras* after each character; one run when there are none."""
    string = text.decode("latin-1")
    if not any(extra != (0.0, 0.0) for extra in extras):
        _advance(machine, *_run(machine, string))
        return
    for char, (ex, ey) in zip(string, extras, strict=True):
        dx, dy = _run(machine, char)
        _advance(machine, dx + ex, dy + ey)


def _show(machine: _Machine, _: int) -> None:
    """``show``."""
    text = machine.pop(1, bytes)[0]
    _show_spaced(machine, text, [(0.0, 0.0)] * len(text))


def _ashow(machine: _Machine, _: int) -> None:
    """``ashow``: extra advance (ax, ay) after every character."""
    ax, ay, text = machine.pop(3, (float, bytes))
    if not isinstance(text, bytes):
        raise _Underflow
    _show_spaced(machine, text, [(ax, ay)] * len(text))


def _widthshow(machine: _Machine, _: int) -> None:
    """``widthshow``: extra advance (cx, cy) after each occurrence of one character code."""
    cx, cy, code, text = machine.pop(4, (float, bytes))
    if not isinstance(text, bytes):
        raise _Underflow
    _show_spaced(machine, text, [(cx, cy) if char == int(code) else (0.0, 0.0) for char in text])


def _awidthshow(machine: _Machine, _: int) -> None:
    """``awidthshow``: ``widthshow`` plus (ax, ay) after every character."""
    cx, cy, code, ax, ay, text = machine.pop(6, (float, bytes))
    if not isinstance(text, bytes):
        raise _Underflow
    _show_spaced(machine, text, [(ax + cx, ay + cy) if char == int(code) else (ax, ay) for char in text])


def _xyshow(machine: _Machine, _: int) -> None:
    """``xyshow``: the advance after each character is the (x, y) pair given for it."""
    text, offsets = machine.pop(2, (bytes, list))
    if not isinstance(text, bytes) or not isinstance(offsets, list):
        raise _Underflow
    for i, char in enumerate(text.decode("latin-1")):
        _run(machine, char)
        pair = offsets[2 * i:2 * i + 2]
        if len(pair) == 2:
            _advance(machine, *pair)


OPERATORS: Final[dict[str, Callable[[_Machine, int], None]]] = {
    "clip": _clip_to_path,
    "eoclip": _clip_to_path,
    "image": _image,
    "colorimage": _colorimage,
    "currentfile": lambda m, _: m.stack.append(_File()),
    "filter": _filter,
    "true": lambda m, _: m.stack.append(True),
    "false": lambda m, _: m.stack.append(False),
    "findfont": _find_font,
    "scalefont": _scale_font,
    "makefont": _make_font,
    "selectfont": _select_font,
    "setfont": _set_font,
    "show": _show,
    "ashow": _ashow,
    "widthshow": _widthshow,
    "awidthshow": _awidthshow,
    "xyshow": _xyshow,
    "moveto": lambda m, _: m.outline.move(m.state.ctm, *m.pop(2)),
    "lineto": lambda m, _: m.outline.line(m.state.ctm, *m.pop(2)),
    "curveto": lambda m, _: m.outline.curve(m.state.ctm, *m.pop(6)),
    "rmoveto": lambda m, _: m.outline.move(m.state.ctm, *m.relative(*m.pop(2))),
    "rlineto": lambda m, _: m.outline.line(m.state.ctm, *m.relative(*m.pop(2))),
    "rcurveto": lambda m, _: m.outline.curve(m.state.ctm, *m.relative(*m.pop(6))),
    "closepath": lambda m, _: m.outline.close(),
    "newpath": lambda m, _: m.outline.take(),
    "arc": lambda m, _: _arc(m, clockwise=False),
    "arcn": lambda m, _: _arc(m, clockwise=True),
    "fill": lambda m, _: m.paint(True),
    "eofill": lambda m, _: m.paint(True, evenodd=True),
    "stroke": lambda m, _: m.paint(False),
    "rectfill": lambda m, _: _rectangle(m, fill=True),
    "rectstroke": lambda m, _: _rectangle(m, fill=False),
    "showpage": lambda m, _: setattr(m, "done", True),
    "setrgbcolor": lambda m, _: setattr(m.state, "color", tuple(m.pop(3))),
    "setgray": lambda m, _: setattr(m.state, "color", (m.pop(1)[0],) * 3),
    "setcmykcolor": lambda m, _: setattr(m.state, "color", cmyk_to_rgb(*m.pop(4))),
    "setlinewidth": _setter("line_width", float),
    "setlinecap": _setter("cap", int),
    "setlinejoin": _setter("join", int),
    "setmiterlimit": _setter("miter", float),
    "setdash": _setdash,
    "gsave": _gsave,
    "grestore": _grestore,
    "save": lambda m, d: (_gsave(m, d), m.stack.append(SAVE_OBJECT)),
    "restore": lambda m, d: (m.pop(1, object), _grestore(m, d)),
    "translate": lambda m, _: m.transform(Matrix.translate(*m.pop(2))),
    "scale": lambda m, _: m.transform(Matrix.scale(*m.pop(2))),
    "rotate": lambda m, _: m.transform(_rotation(m.pop(1)[0])),
    "concat": lambda m, _: m.transform(Matrix(*(float(v) for v in m.pop(1, list)[0][:6]))),
    "dup": lambda m, _: m.stack.extend(m.pop(1, object) * 2),
    "pop": lambda m, _: m.pop(1, object),
    "exch": lambda m, _: m.stack.extend(m.pop(2, object)[::-1]),
    "add": _binary(lambda a, b: a + b),
    "sub": _binary(lambda a, b: a - b),
    "mul": _binary(lambda a, b: a * b),
    "div": _binary(lambda a, b: a / b),
    "neg": lambda m, _: m.stack.append(-m.pop(1)[0]),
    "def": _def,
    "bind": lambda m, _: None,
    "load": _load,
    "exec": _exec,
    "[": lambda m, _: m.stack.append(Mark()),
    "]": lambda m, _: m.stack.append(_to_mark(m)),
    "<<": lambda m, _: m.stack.append(Mark()),
    ">>": _close_dict,
    "dict": lambda m, _: (m.pop(1), m.stack.append({})),
    "begin": _begin,
    "end": _end,
    "currentdict": lambda m, _: m.stack.append(m.dicts[-1]),
}


def _bounding_box(data: bytes) -> tuple[float, float, float, float] | None:
    """``%%HiResBoundingBox`` or ``%%BoundingBox`` as ``(llx, lly, urx, ury)``."""
    for pattern in _BOUNDS_RE.values():
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


def read_eps(data: bytes) -> Document:
    """Read the paths, images and text an EPS or PostScript program paints as elements.

    Parameters
    ----------
    data : bytes
        The PostScript program, optionally inside a DOS EPS binary wrapper.

    Returns
    -------
    Document
        The drawing in points with y pointing down, sized to ``%%HiResBoundingBox``
        or ``%%BoundingBox`` when present and fitted to the content otherwise.

    Raises
    ------
    ValueError
        If *data* does not start with ``%!``.

    See Also
    --------
    svgwriter.export._vector._pdf_read.read_pdf : Read PDF pages.

    Notes
    -----
    A tokenizer and stack machine for a subset of PostScript: numbers, names,
    literal names, strings, arrays and procedures ``{}`` with ``def``,
    ``bind``, ``load`` and ``exec``; dictionaries (``dict``, ``<<``/``>>``,
    ``begin``, ``end``, ``currentdict``) for scoping definitions; the path operators ``moveto lineto
    curveto rmoveto rlineto rcurveto closepath newpath arc arcn``; painting
    with ``fill eofill stroke rectfill rectstroke``; ``setrgbcolor setgray
    setcmykcolor``; ``setlinewidth setlinecap setlinejoin setmiterlimit
    setdash``; ``gsave grestore save restore translate scale rotate concat``;
    and ``dup pop exch add sub mul div neg``. Reading stops at the first
    ``showpage``. Unknown operators are ignored and an operator that finds
    too few operands is skipped, so a program using more of the language
    reads as far as this subset reaches.

    Also read: 8-bit ``image`` (gray, five operands) and ``colorimage``
    (gray, RGB, CMYK; one source or one per component) from ``currentfile``
    with ``/ASCIIHexDecode filter`` or from procedures returning strings,
    placed as ``<image>`` through the current transform and the image
    matrix; text with ``findfont scalefont makefont setfont selectfont`` and
    ``show ashow widthshow awidthshow xyshow`` as ``<text>`` at the current
    point (family from the font name, ``-Bold``/``-Italic`` as weight and
    style, advance from the measured width); and ``clip``/``eoclip``,
    intersected with the current clip and kept by ``gsave``/``grestore``
    (``eoclip`` clips with the nonzero rule). Image data inline in a
    procedure body, other bit depths and image dictionaries are skipped, as
    is control flow (``if``, ``loop``, ...).

    Examples
    --------
    >>> from svgwriter.export._vector._eps_read import read_eps
    >>> doc = read_eps(b"%!PS\\n%%BoundingBox: 0 0 10 10\\n1 0 0 setrgbcolor 0 0 10 5 rectfill")
    >>> doc[0].get("fill"), doc[0].bounds()
    ('#ff0000', BBox(x=0.0, y=5.0, width=10.0, height=5.0))
    """
    data = _postscript(data)
    box = _bounding_box(data)
    llx, lly, urx, ury = box if box is not None else (0.0, 0.0, 0.0, 0.0)
    machine = _Machine(Matrix(1.0, 0.0, 0.0, -1.0, -llx, ury))
    machine.execute(_parse(data))
    return to_document(machine.shapes, None if box is None else (0.0, 0.0, urx - llx, ury - lly))
