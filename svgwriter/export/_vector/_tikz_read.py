"""
Reading TikZ pictures back into a document of paths.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Final

from ...color.color import as_color
from ...transform.matrix import IDENTITY, Matrix
from ._reading import BLACK, Outline, Shape, cmyk_to_rgb, to_document

if TYPE_CHECKING:
    from ...document import Document
    from ._reading import RGB

__all__ = ["read_tikz"]

Point = tuple[float, float]
Pair = tuple[str, str | None]

TEX_PT_PER_INCH: Final = 72.27
UNITS: Final = {"pt": 1.0, "bp": TEX_PT_PER_INCH / 72.0, "in": TEX_PT_PER_INCH, "cm": TEX_PT_PER_INCH / 2.54,
                "mm": TEX_PT_PER_INCH / 25.4, "pc": 12.0, "em": 10.0, "ex": 4.3}
DEFAULT_UNIT: Final = UNITS["cm"]
DEFAULT_LINE_WIDTH: Final = 0.4
LINE_WIDTHS: Final = {"ultra thin": 0.1, "very thin": 0.2, "thin": 0.4, "semithick": 0.6, "thick": 0.8,
                      "very thick": 1.2, "ultra thick": 1.6}
DASHES: Final = {"dashed": (3.0, 3.0), "densely dashed": (3.0, 2.0), "loosely dashed": (3.0, 6.0),
                 "dotted": (DEFAULT_LINE_WIDTH, 2.0), "densely dotted": (DEFAULT_LINE_WIDTH, 1.0),
                 "loosely dotted": (DEFAULT_LINE_WIDTH, 4.0), "solid": ()}
CAPS: Final = {"butt": "butt", "round": "round", "rect": "square"}
XCOLOR: Final = {
    "red": (1.0, 0.0, 0.0), "green": (0.0, 1.0, 0.0), "blue": (0.0, 0.0, 1.0), "cyan": (0.0, 1.0, 1.0),
    "magenta": (1.0, 0.0, 1.0), "yellow": (1.0, 1.0, 0.0), "black": BLACK, "white": (1.0, 1.0, 1.0),
    "gray": (0.5, 0.5, 0.5), "darkgray": (0.25, 0.25, 0.25), "lightgray": (0.75, 0.75, 0.75),
    "brown": (0.75, 0.5, 0.25), "lime": (0.75, 1.0, 0.0), "olive": (0.5, 0.5, 0.0), "orange": (1.0, 0.5, 0.0),
    "pink": (1.0, 0.75, 0.75), "purple": (0.75, 0.0, 0.25), "teal": (0.0, 0.5, 0.5), "violet": (0.5, 0.0, 0.5),
}
COMMAND_PAINTS: Final = {"draw": (False, True), "fill": (True, False), "filldraw": (True, True),
                         "path": (False, False), "useasboundingbox": (False, False)}
RGB_SCALE: Final = 255.0
PERCENT: Final = 100.0
FULL_TURN: Final = 2 * math.pi
_COMMENT_RE: Final = re.compile(r"(?<!\\)%[^\n]*")
NODE_FONT_SIZE: Final = 10.0
NODE_BASELINE: Final = 0.35
NODE_TEXT_HEIGHT: Final = 0.8 * NODE_FONT_SIZE
INNER_SEP: Final = 3.333
MAX_STYLE_DEPTH: Final = 8
MAX_LOOPS: Final = 1000
MAX_LOOP_ITEMS: Final = 10000
DIAGONAL: Final = math.sqrt(0.5)
NODE_SHAPES: Final = ("circle", "rectangle", "ellipse")
ANCHORS: Final = {"center": (0, 0), "north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0),
                  "north east": (1, -1), "north west": (-1, -1), "south east": (1, 1), "south west": (-1, 1)}
POSITIONS: Final = {"above": "south", "below": "north", "left": "east", "right": "west",
                    "above left": "south east", "above right": "south west",
                    "below left": "north east", "below right": "north west"}
NODE_POSITIONS: Final = {"midway": 0.5, "near start": 0.25, "near end": 0.75, "very near start": 0.125,
                         "very near end": 0.875, "at start": 0.0, "at end": 1.0}
_MARKUP_RE: Final = re.compile(r"\\[A-Za-z]+\*?\{([^{}]*)\}")
_SPACE_RE: Final = re.compile(r"\s+")
_EVENT_RE: Final = re.compile(r"\\(?:(begin|end)\s*\{scope\}|(filldraw|draw|fill|path|useasboundingbox|node|coordinate)"
                              r"(?![A-Za-z]))")
NODE_COMMANDS: Final = ("node", "coordinate")
_FOREACH_RE: Final = re.compile(r"\\foreach\s+(\\[A-Za-z]+(?:\s*/\s*\\[A-Za-z]+)*)\s+in\s*")
_MACRO_RE: Final = re.compile(r"\\[A-Za-z]+")
_TIKZSET_RE: Final = re.compile(r"\\tikzset\s*\{")
_TIKZSTYLE_RE: Final = re.compile(r"\\tikzstyle\s*\{([^}]*)\}\s*=\s*\[")
_DEFINECOLOR_RE: Final = re.compile(r"\\definecolor\s*\{([^}]*)\}\s*\{([^}]*)\}\s*\{([^}]*)\}")
_COLORLET_RE: Final = re.compile(r"\\colorlet\s*\{([^}]*)\}\s*\{([^}]*)\}")
_PICTURE_RE: Final = re.compile(r"\\begin\s*\{tikzpicture\}")
_DIMENSION_RE: Final = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\.\d+))\s*([a-z]{2})?\s*$")
_PATH_TOKEN_RE: Final = re.compile(r"\s*(\+\+|\+|--|\|-|-\||\.\.|[A-Za-z]+|.)", re.S)
_DASH_RE: Final = re.compile(r"(?:on|off)\s+([+-]?(?:\d+\.?\d*|\.\d+)\s*(?:[a-z]{2}(?![a-z]))?)")
BRACKETS: Final = {"(": ")", "[": "]", "{": "}"}


def _balanced(text: str, start: int) -> tuple[str, int]:
    """The text inside the bracket opening at *start*, and the index after its closer."""
    opener, closer = text[start], BRACKETS[text[start]]
    depth = 0
    for i in range(start, len(text)):
        depth += (text[i] == opener) - (text[i] == closer)
        if depth == 0:
            return text[start + 1:i], i + 1
    return text[start + 1:], len(text)


def _unbrace(text: str) -> str:
    """*text* without one pair of braces wrapping all of it."""
    text = text.strip()
    if text.startswith("{") and _balanced(text, 0)[1] == len(text):
        return text[1:-1].strip()
    return text


def _split(text: str) -> list[str]:
    """Split *text* at commas outside braces, brackets and parentheses."""
    parts, depth, current = [], 0, []
    for char in text:
        depth += (char in "{[(") - (char in "}])")
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [_unbrace(part) for part in parts if part.strip()]


def _options(text: str) -> list[Pair]:
    """``key=value`` pairs of an option list; bare keys have the value None."""
    out = []
    for part in _split(text):
        key, separator, value = part.partition("=")
        out.append((" ".join(key.split()), _unbrace(value) if separator else None))
    return out


def _expand(pairs: list[Pair], styles: dict[str, list[Pair]], depth: int = 0) -> list[Pair]:
    """*pairs* with every bare style name replaced by the options it defines."""
    out: list[Pair] = []
    for key, value in pairs:
        if value is None and key in styles and depth < MAX_STYLE_DEPTH:
            out += _expand(styles[key], styles, depth + 1)
        else:
            out.append((key, value))
    return out


def _define(table: dict[str, list[Pair]], pairs: list[Pair]) -> None:
    """Record the ``name/.style`` and ``name/.append style`` entries of *pairs* in *table*."""
    for key, value in pairs:
        name, _, kind = key.partition("/.")
        if value is None or kind not in ("style", "append style"):
            continue
        table[name] = (table.get(name, []) if kind == "append style" else []) + _options(value)


def _style_table(text: str, picture: str) -> dict[str, list[Pair]]:
    """Styles from ``\\tikzset``, ``\\tikzstyle`` and the picture's own options, by name."""
    table: dict[str, list[Pair]] = {}
    for match in _TIKZSET_RE.finditer(text):
        _define(table, _options(_balanced(text, match.end() - 1)[0]))
    for match in _TIKZSTYLE_RE.finditer(text):
        table[match.group(1).strip()] = _options(_balanced(text, match.end() - 1)[0])
    _define(table, _options(picture))
    return table


def _dimension(text: str) -> tuple[float, bool]:
    """A length in points and whether it carried a unit."""
    match = _DIMENSION_RE.match(text)
    if match is None:
        raise ValueError(f"not a TikZ dimension: {text!r}")
    value, unit = float(match.group(1)), match.group(2)
    if unit is not None and unit not in UNITS:
        raise ValueError(f"unknown TeX unit: {unit!r}")
    return value * UNITS.get(unit or "pt", 1.0), unit is not None


@dataclass
class _Frame:
    """The picture's coordinate system: unit vectors and scale, mapped to y-down points."""

    x_unit: float = DEFAULT_UNIT
    y_unit: float = DEFAULT_UNIT
    x_scale: float = 1.0
    y_scale: float = 1.0
    matrix: Matrix = IDENTITY

    def vector(self, text: str) -> Point:
        """SVG offset of a coordinate ``x,y`` or ``angle:radius``, through the scope transform."""
        x, y = self._raw(text)
        m = self.matrix
        return m.a * x + m.c * y, m.b * x + m.d * y

    def absolute(self, text: str) -> Point:
        """SVG position of a coordinate, through the scope transform."""
        x, y = self.vector(text)
        return x + self.matrix.e, y + self.matrix.f

    def scoped(self, pairs: list[Pair]) -> _Frame:
        """The frame inside a scope with these options: ``shift``, ``xshift``, ``yshift``, ``scale``, ``rotate``."""
        matrix = self.matrix
        for key, value in pairs:
            try:
                step = self._step(key, value or "")
            except ValueError:
                continue
            matrix = matrix if step is None else matrix @ step
        return replace(self, matrix=matrix)

    def _step(self, key: str, value: str) -> Matrix | None:
        """The transform one scope option adds, None for other options."""
        if key == "shift":
            return Matrix.translate(*self._raw(_balanced(value, 0)[0] if value.startswith("(") else value))
        if key in ("xshift", "yshift"):
            offset = _dimension(value)[0]
            return Matrix.translate(offset, 0.0) if key == "xshift" else Matrix.translate(0.0, -offset)
        if key == "rotate":
            return Matrix.rotate(-float(value))
        if key in ("scale", "xscale", "yscale"):
            factor = float(value)
            return Matrix.scale(1.0 if key == "yscale" else factor, 1.0 if key == "xscale" else factor)
        return None

    def _raw(self, text: str) -> Point:
        """Offset of a coordinate in the picture's axes."""
        if ":" in text and "," not in text:
            angle, radius = text.split(":", 1)
            r, unit = _dimension(radius)
            a = math.radians(float(angle))
            return self._map(r * math.cos(a), r * math.sin(a), unit, unit)
        parts = _split(text)
        if len(parts) != 2:
            raise ValueError(f"unsupported TikZ coordinate: ({text})")
        (x, x_unit), (y, y_unit) = _dimension(parts[0]), _dimension(parts[1])
        return self._map(x, y, x_unit, y_unit)

    def radii(self, x: str, y: str) -> Point:
        """Ellipse radii in SVG units."""
        (rx, x_unit), (ry, y_unit) = _dimension(x), _dimension(y)
        m = self.matrix
        return (abs(rx * self.x_scale * (1.0 if x_unit else self.x_unit)) * math.hypot(m.a, m.b),
                abs(ry * self.y_scale * (1.0 if y_unit else self.y_unit)) * math.hypot(m.c, m.d))

    def _map(self, x: float, y: float, x_unit: bool, y_unit: bool) -> Point:
        """Scale a coordinate and flip y; unitless components use the unit vectors."""
        return (x * self.x_scale * (1.0 if x_unit else self.x_unit),
                -y * self.y_scale * (1.0 if y_unit else self.y_unit))


def _picture_options(text: str) -> str:
    """The option list of the first ``tikzpicture`` environment, empty when it has none."""
    match = _PICTURE_RE.search(text)
    if match is None:
        return ""
    start = match.end() + len(text[match.end():]) - len(text[match.end():].lstrip())
    if start >= len(text) or text[start] != "[":
        return ""
    return _balanced(text, start)[0]


def _frame(options: str) -> _Frame:
    """The frame set by a ``tikzpicture``'s ``x``, ``y`` and scale options."""
    frame = _Frame()
    for key, value in _options(options):
        try:
            if key in ("x", "y") and value is not None:
                setattr(frame, f"{key}_unit", _dimension(value)[0])
            elif key in ("scale", "xscale", "yscale") and value is not None:
                for axis in ("x", "y") if key == "scale" else (key[0],):
                    setattr(frame, f"{axis}_scale", getattr(frame, f"{axis}_scale") * float(value))
        except ValueError:
            continue
    return frame


def _mix(expression: str, colors: dict[str, RGB]) -> RGB:
    """An xcolor expression such as ``red``, ``red!30`` or ``red!30!blue``."""
    parts = [part.strip() for part in expression.split("!")]
    color = _named(parts[0], colors)
    for i in range(1, len(parts), 2):
        share = float(parts[i]) / PERCENT
        other = _named(parts[i + 1], colors) if i + 1 < len(parts) else XCOLOR["white"]
        color = tuple(share * a + (1 - share) * b for a, b in zip(color, other, strict=True))
    return color


def _named(name: str, colors: dict[str, RGB]) -> RGB:
    """A colour by name: defined, xcolor base, then SVG keyword."""
    if name in colors:
        return colors[name]
    if name in XCOLOR:
        return XCOLOR[name]
    return as_color(name).rgb


def _values(spec: str) -> list[float]:
    """Comma-separated numbers of a colour specification."""
    return [float(v) for v in spec.split(",")]


COLOR_MODELS: Final[dict[str, Callable[[str], tuple[float, ...]]]] = {
    "RGB": lambda spec: tuple(c / RGB_SCALE for c in _values(spec)),
    "rgb": lambda spec: tuple(_values(spec)),
    "gray": lambda spec: (_values(spec)[0],) * 3,
    "cmyk": lambda spec: cmyk_to_rgb(*_values(spec)),
    "HTML": lambda spec: as_color("#" + spec).rgb,
}


def _definitions(text: str) -> dict[str, RGB]:
    """Colours from ``\\definecolor`` (``RGB``, ``rgb``, ``HTML``, ``gray``, ``cmyk``) and ``\\colorlet``."""
    colors: dict[str, RGB] = {}
    for name, model, spec in _DEFINECOLOR_RE.findall(text):
        try:
            color = COLOR_MODELS[model.strip()](spec.strip())
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        if len(color) == len(BLACK):
            colors[name.strip()] = color
    for name, expression in _COLORLET_RE.findall(text):
        try:
            colors[name.strip()] = _mix(expression, colors)
        except ValueError:
            continue
    return colors


@dataclass
class _Style:
    """Paint and line options accumulated from a command and its option list."""

    fill: bool
    draw: bool
    colors: dict[str, RGB]
    color: RGB = BLACK
    text_color: RGB | None = None
    fill_color: RGB | None = None
    draw_color: RGB | None = None
    fill_opacity: float = 1.0
    draw_opacity: float = 1.0
    line_width: float = DEFAULT_LINE_WIDTH
    linecap: str = "butt"
    linejoin: str = "miter"
    miter_limit: float = 10.0
    evenodd: bool = False
    dashes: tuple[float, ...] = field(default=())

    def paint(self, key: str, value: str | None) -> None:
        """``draw``/``fill``, bare or with a colour or ``none``."""
        enabled = value != "none"
        setattr(self, key, enabled)
        if enabled and value is not None:
            setattr(self, f"{key}_color", _mix(value, self.colors))

    def shape(self, ops: list) -> Shape:
        """A shape painting *ops* with this style."""
        return Shape(ops, fill=(self.fill_color or self.color) if self.fill else None,
                     stroke=(self.draw_color or self.color) if self.draw else None,
                     fill_opacity=self.fill_opacity, stroke_opacity=self.draw_opacity, evenodd=self.evenodd,
                     stroke_width=self.line_width, linecap=self.linecap, linejoin=self.linejoin,
                     miter_limit=self.miter_limit, dashes=self.dashes)


def _opacity(style: _Style, value: str | None) -> None:
    """``opacity``: the same opacity for fill and stroke."""
    style.fill_opacity = style.draw_opacity = float(value or 1)


def _dash_pattern(value: str | None) -> tuple[float, ...]:
    """Dash lengths of ``on <len> off <len> ...``."""
    return tuple(_dimension(v)[0] for v in _DASH_RE.findall(value or ""))


OPTIONS: Final[dict[str, Callable[[_Style, str | None], None]]] = {
    "draw": lambda s, v: s.paint("draw", v),
    "fill": lambda s, v: s.paint("fill", v),
    "color": lambda s, v: setattr(s, "color", _mix(v or "black", s.colors)),
    "text": lambda s, v: setattr(s, "text_color", _mix(v or "black", s.colors)),
    "line width": lambda s, v: setattr(s, "line_width", _dimension(v or "0.4pt")[0]),
    "opacity": _opacity,
    "fill opacity": lambda s, v: setattr(s, "fill_opacity", float(v or 1)),
    "draw opacity": lambda s, v: setattr(s, "draw_opacity", float(v or 1)),
    "line cap": lambda s, v: setattr(s, "linecap", CAPS[v or "butt"]),
    "line join": lambda s, v: setattr(s, "linejoin", v or "miter"),
    "miter limit": lambda s, v: setattr(s, "miter_limit", float(v or 10)),
    "even odd rule": lambda s, v: setattr(s, "evenodd", True),
    "nonzero rule": lambda s, v: setattr(s, "evenodd", False),
    "dash pattern": lambda s, v: setattr(s, "dashes", _dash_pattern(v)),
    **{name: lambda s, v, w=width: setattr(s, "line_width", w) for name, width in LINE_WIDTHS.items()},
    **{name: lambda s, v, d=dashes: setattr(s, "dashes", d) for name, dashes in DASHES.items()},
}


def _style(command: str, options: list[Pair], colors: dict[str, RGB]) -> _Style:
    """The style of a command: its implied paints, then each option in order."""
    fill, draw = COMMAND_PAINTS[command]
    style = _Style(fill=fill, draw=draw, colors=colors)
    for key, value in options:
        try:
            if key in OPTIONS:
                OPTIONS[key](style, value)
            elif value is None:
                style.color = _mix(key, colors)
        except (ValueError, KeyError):
            continue
    return style


def _tokens(text: str) -> list[tuple[str, str]]:
    """Path tokens: ``("coord"|"opts"|"text", body)`` for bracketed groups, else ``("op", word)``."""
    tokens, pos = [], 0
    kinds = {"(": "coord", "[": "opts", "{": "text"}
    while pos < len(text):
        match = _PATH_TOKEN_RE.match(text, pos)
        if match is None or not match.group(1).strip():
            break
        word, start = match.group(1), match.start(1)
        if word in kinds:
            body, pos = _balanced(text, start)
            tokens.append((kinds[word], body))
            continue
        pos = match.end()
        tokens.append(("op", word))
    return tokens


@dataclass(frozen=True)
class _Place:
    """A named node or coordinate: its centre and, for shaped nodes, the half sizes of its border."""

    x: float
    y: float
    shape: str = "rectangle"
    half_width: float = 0.0
    half_height: float = 0.0

    def anchor(self, name: str) -> Point:
        """The border point at a compass anchor; diagonals of round shapes lie on the curve."""
        try:
            ux, uy = ANCHORS[name]
        except KeyError:
            raise ValueError(f"unknown anchor: {name!r}") from None
        scale = DIAGONAL if ux and uy and self.shape != "rectangle" else 1.0
        return self.x + ux * self.half_width * scale, self.y + uy * self.half_height * scale


@dataclass
class _Context:
    """What a picture shares between its commands: colours, styles and the nodes named so far."""

    colors: dict[str, RGB]
    styles: dict[str, list[Pair]]
    places: dict[str, _Place] = field(default_factory=dict)


@dataclass(frozen=True)
class _Scope:
    """The coordinate frame and the options in force inside a scope."""

    frame: _Frame
    pairs: list[Pair]

    def child(self, pairs: list[Pair]) -> _Scope:
        """The scope opened inside this one with *pairs*."""
        return _Scope(self.frame.scoped(pairs), self.pairs + pairs)


class _PathReader:
    """Turns path tokens into outline operations in SVG coordinates, and its nodes into extra shapes."""

    def __init__(self, frame: _Frame, context: _Context, options: list[Pair]) -> None:
        self.frame = frame
        self.context = context
        self.inherited = [(key, value) for key, value in options if key not in ("draw", "fill")]
        self.outline = Outline()
        self.extras: list[Any] = []
        self.last: Point = (frame.matrix.e, frame.matrix.f)
        self.base: Point = self.last
        self.span: list[Point] | None = None
        self.lifted = True

    def read(self, tokens: list[tuple[str, str]]) -> list:
        """The operations of a whole path."""
        i, connector, prefix = 0, None, None
        while i < len(tokens):
            kind, body = tokens[i]
            i += 1
            if kind == "coord":
                self.segment(connector, self.point(body, prefix))
                connector = prefix = None
            elif kind != "op":
                continue
            elif body in ("+", "++"):
                prefix = body
            elif body in ("--", "|-", "-|", "rectangle"):
                connector = body
            elif body == "..":
                connector, i = self.controls(tokens, i)
            elif body == "cycle":
                self.cycle(connector)
                connector = None
            elif body in ("circle", "ellipse"):
                i = self.ellipse(tokens, i)
            elif body in ("node", "coordinate"):
                i = self.node(body == "coordinate", tokens, i)
        return self.outline.take()

    def lookup(self, body: str) -> Point | None:
        """The position of a named node or coordinate, ``name`` or ``name.anchor``; None for other text."""
        name = body.strip()
        place = self.context.places.get(name)
        if place is not None:
            return place.x, place.y
        base, _, anchor = name.rpartition(".")
        place = self.context.places.get(base)
        return place.anchor(anchor) if place is not None else None

    def point(self, body: str, prefix: str | None) -> Point:
        """A path point; ``++`` moves the base of later relative points, ``+`` does not."""
        named = self.lookup(body)
        if named is not None:
            self.base = named
            return named
        if prefix is None:
            self.base = self.frame.absolute(body)
            return self.base
        dx, dy = self.frame.vector(body)
        point = (self.base[0] + dx, self.base[1] + dy)
        if prefix == "++":
            self.base = point
        return point

    def pen(self) -> None:
        """Start a subpath at the last point if the pen is lifted."""
        if self.lifted:
            self.outline.move(IDENTITY, *self.last)
            self.lifted = False

    def segment(self, connector: str | tuple | None, point: Point) -> None:
        """Connect the last point to *point*."""
        (x0, y0), (x, y) = self.last, point
        self.span = None
        if connector is None:
            self.lifted = True
        elif connector == "rectangle":
            self.outline.rect(IDENTITY, x0, y0, x - x0, y - y0)
            self.lifted = True
        elif isinstance(connector, tuple):
            self.pen()
            self.span = self.curve(connector, point)
        else:
            self.pen()
            corner = {"|-": (x0, y), "-|": (x, y0)}.get(connector)
            if corner is not None:
                self.outline.line(IDENTITY, *corner)
            self.outline.line(IDENTITY, x, y)
            self.span = [(x0, y0), point]
        self.last = point

    def along(self, fraction: float) -> Point:
        """The point at *fraction* of the last segment (its start at 0), the current point without one."""
        if self.span is None:
            return self.last
        points = self.span
        while len(points) > 1:
            points = [(a[0] + fraction * (b[0] - a[0]), a[1] + fraction * (b[1] - a[1]))
                      for a, b in zip(points, points[1:], strict=False)]
        return points[0]

    def controls(self, tokens: list[tuple[str, str]], i: int) -> tuple[tuple | str, int]:
        """``.. controls (a) [and (b)] ..`` read after the first ``..``; a bare ``..`` acts as ``--``."""
        if i >= len(tokens) or tokens[i] != ("op", "controls"):
            return "--", i
        first, i = self.control(tokens, i + 1)
        second = first
        if i < len(tokens) and tokens[i] == ("op", "and"):
            second, i = self.control(tokens, i + 1)
        if i < len(tokens) and tokens[i] == ("op", ".."):
            i += 1
        return ("curve", first, second), i

    def control(self, tokens: list[tuple[str, str]], i: int) -> tuple[tuple[Point, bool], int]:
        """A control point and whether it is ``+``/``++`` relative."""
        relative = tokens[i] in (("op", "+"), ("op", "++"))
        kind, body = tokens[i + relative]
        if kind != "coord":
            raise ValueError("control point expected")
        offset = self.frame.vector(body) if relative else self.lookup(body) or self.frame.absolute(body)
        return (offset, relative), i + relative + 1

    def curve(self, connector: tuple, end: Point) -> list[Point]:
        """Cubic to *end*, returning its four points; a relative first control is taken from the start, a
        relative second from *end*."""
        controls = []
        for ((dx, dy), relative), anchor in zip(connector[1:], (self.last, end), strict=True):
            controls.append((anchor[0] + dx, anchor[1] + dy) if relative else (dx, dy))
        self.outline.curve(IDENTITY, *controls[0], *controls[1], *end)
        return [self.last, *controls, end]

    def cycle(self, connector: str | tuple | None) -> None:
        """Close the subpath, along a curve when one is pending."""
        start = self.outline.start
        if start is None or self.lifted:
            return
        if isinstance(connector, tuple):
            self.curve(connector, start)
        self.outline.close()
        self.last, self.lifted = start, True

    def node(self, coordinate: bool, tokens: list[tuple[str, str]], i: int) -> int:
        """A ``node`` or ``coordinate`` read after its keyword: placed ``at`` a point, along the last segment
        for ``pos``/``midway``, or at the current point; its text, border and name become extra shapes and places."""
        from ...elements.text import Text
        from ._reading import _hex

        pairs, name, at, content, i = _read_node(tokens, i, coordinate)
        styles = self.context.styles
        every = _expand(styles.get("every node", []), styles)
        options = self.inherited + every + _expand(pairs, styles)
        keys = dict(options)
        fraction = float(keys["pos"]) if keys.get("pos") else next((f for k, f in NODE_POSITIONS.items() if k in keys), None)
        if at is not None:
            x, y = self.lookup(at) or self.frame.absolute(at)
        else:
            x, y = self.last if fraction is None else self.along(fraction)
        label = "" if coordinate else _plain(content or "")
        shape, half_width, half_height = ("rectangle", 0.0, 0.0) if coordinate else _geometry(label, keys)
        anchor, distance = keys.get("anchor") or "center", 0.0
        for key, anchor_name in POSITIONS.items():
            if key in keys:
                anchor, distance = anchor_name, _length(keys, key, 0.0)
        ax, ay = _Place(0.0, 0.0, shape, half_width, half_height).anchor(anchor)
        ux, uy = ANCHORS[anchor]
        x += _length(keys, "xshift", 0.0) - ax - ux * distance
        y += -_length(keys, "yshift", 0.0) - ay - uy * distance
        if name:
            self.context.places[name] = _Place(x, y, shape, half_width, half_height)
        if coordinate:
            return i
        style = _style("path", options, self.context.colors)
        if style.draw or style.fill:
            outline = Outline()
            if shape == "rectangle":
                outline.rect(IDENTITY, x - half_width, y - half_height, 2 * half_width, 2 * half_height)
            else:
                outline.arc(IDENTITY, (x, y), (half_width, half_height), 0.0, FULL_TURN, connect=False)
                outline.close()
            self.extras.append(style.shape(outline.take()))
        if label:
            self.extras.append(Text(label, x=x, y=y + NODE_FONT_SIZE * NODE_BASELINE, font_size=NODE_FONT_SIZE,
                                    text_anchor="middle", fill=_hex(style.text_color or style.color)))
        return i

    def ellipse(self, tokens: list[tuple[str, str]], i: int) -> int:
        """``circle``/``ellipse`` about the last point, sized by ``[radius=r]`` or ``(r)``/``(a and b)``."""
        radii = None
        if i < len(tokens) and tokens[i][0] == "opts":
            options = dict(_options(tokens[i][1]))
            x, y = options.get("x radius", options.get("radius")), options.get("y radius", options.get("radius"))
            radii = self.frame.radii(x, y) if x and y else None
            i += 1
        if radii is None and i < len(tokens) and tokens[i][0] == "coord":
            x, _, y = tokens[i][1].partition(" and ")
            radii = self.frame.radii(x, y or x)
            i += 1
        if radii is None:
            raise ValueError("circle without a radius")
        self.outline.arc(IDENTITY, self.last, radii, 0.0, FULL_TURN, connect=False)
        self.outline.close()
        self.lifted = True
        return i


def _read_node(tokens: list[tuple[str, str]], i: int, coordinate: bool) -> tuple[list[Pair], str, str | None, str | None, int]:
    """Options, name, ``at`` coordinate, text and the next index of the node starting at token *i*."""
    pairs: list[Pair] = []
    name, at, content = "", None, None
    while i < len(tokens):
        kind, body = tokens[i]
        if kind == "opts":
            pairs += _options(body)
        elif kind == "coord" and not name:
            name = body.strip()
        elif (kind, body) == ("op", "at") and i + 1 < len(tokens) and tokens[i + 1][0] == "coord":
            at, i = tokens[i + 1][1], i + 1
        elif kind == "text" and not coordinate:
            return pairs, name, at, body, i + 1
        else:
            break
        i += 1
    return pairs, name, at, content, i


def _length(keys: dict[str, str | None], name: str, default: float) -> float:
    """The length option *name* in points, *default* when absent or unreadable."""
    value = keys.get(name)
    try:
        return default if value is None else _dimension(value)[0]
    except ValueError:
        return default


def _geometry(label: str, keys: dict[str, str | None]) -> tuple[str, float, float]:
    """The shape of a node and its half width and half height, from the text size, ``inner sep`` and minimums."""
    from ...ops.text import text_width

    sep = _length(keys, "inner sep", INNER_SEP)
    width = (text_width(label, size=NODE_FONT_SIZE) if label else 0.0) + 2 * _length(keys, "inner xsep", sep)
    height = (NODE_TEXT_HEIGHT if label else 0.0) + 2 * _length(keys, "inner ysep", sep)
    size = _length(keys, "minimum size", 0.0)
    least_width, least_height = (max(size, _length(keys, f"minimum {axis}", 0.0)) / 2 for axis in ("width", "height"))
    shape = keys.get("shape") if keys.get("shape") in NODE_SHAPES else next((k for k in NODE_SHAPES if k in keys), "rectangle")
    if shape == "circle":
        radius = max(math.hypot(width, height) / 2, least_width, least_height)
        return shape, radius, radius
    if shape == "ellipse":
        return shape, max(width * DIAGONAL, least_width), max(height * DIAGONAL, least_height)
    return shape, max(width / 2, least_width), max(height / 2, least_height)


def _statement(text: str, start: int) -> tuple[str, int]:
    """The path text from *start* up to the ``;`` outside brackets."""
    depth = 0
    for i in range(start, len(text)):
        char = text[i]
        depth += (char in "{[(") - (char in "}])")
        if char == ";" and depth <= 0:
            return text[start:i], i + 1
    return text[start:], len(text)


def _events(text: str) -> list[tuple[str, str, str, str]]:
    """``(kind, command, options, path)`` in order: ``begin``/``end`` of scopes and ``cmd`` for path commands.

    A ``\\node`` or ``\\coordinate`` is read as ``\\path node ...``: its options stay in its path.
    """
    out, pos = [], 0
    while (match := _EVENT_RE.search(text, pos)) is not None:
        pos = match.end() + len(text[match.end():]) - len(text[match.end():].lstrip())
        command, options = match.group(2) or "", ""
        if match.group(1) == "end":
            out.append(("end", "", "", ""))
            continue
        if command in NODE_COMMANDS:
            body, pos = _statement(text, match.end())
            out.append(("cmd", command, "", command + body))
            continue
        if pos < len(text) and text[pos] == "[":
            options, pos = _balanced(text, pos)
        if match.group(1):
            out.append(("begin", "", options, ""))
            continue
        body, pos = _statement(text, pos)
        out.append(("cmd", command, options, body))
    return out


def _loop_items(text: str) -> list[str]:
    """The values of a ``\\foreach`` list, with ``a,b,...,z`` expanded as an arithmetic progression."""
    parts = _split(text)
    if "..." not in parts:
        return parts
    k = parts.index("...")
    head, stop = [float(part) for part in parts[:k]], float(parts[k + 1])
    step = head[-1] - head[-2] if len(head) > 1 else math.copysign(1.0, stop - head[0])
    count = math.floor((stop - head[0]) / step + 1e-9) + 1
    if count > MAX_LOOP_ITEMS:
        raise ValueError("\\foreach list too long")
    return [f"{head[0] + j * step:g}" for j in range(count)]


def _unrolled(text: str, match: re.Match[str]) -> tuple[str, int]:
    """The repeated body of the ``\\foreach`` at *match*, and the index where the loop ends."""
    names = _MACRO_RE.findall(match.group(1))
    if text[match.end()] != "{":
        raise ValueError("\\foreach list must be in braces")
    items, pos = _balanced(text, match.end())
    pos += len(text[pos:]) - len(text[pos:].lstrip())
    if text[pos] == "{":
        body, end = _balanced(text, pos)
    else:
        body, end = _statement(text, pos)
        body += ";"
    copies = []
    for item in _loop_items(items):
        values = dict(zip(names, item.split("/") if len(names) > 1 else [item], strict=False))
        copies.append(_MACRO_RE.sub(lambda m, v=values: v.get(m.group(), m.group()), body))
    return "\n".join(copies), end


def _unroll(text: str) -> str:
    """*text* with each ``\\foreach`` replaced by its body once per value, the variable substituted."""
    for _ in range(MAX_LOOPS):
        match = _FOREACH_RE.search(text)
        if match is None:
            break
        try:
            body, end = _unrolled(text, match)
        except (ValueError, IndexError):
            body, end = "", match.end()
        text = text[:match.start()] + body + text[end:]
    return text


def _bounds(ops: list) -> tuple[float, float, float, float] | None:
    """``(min_x, min_y, width, height)`` of the points in *ops*, None when empty or flat."""
    xs = [v for _, args in ops for v in args[0::2]]
    ys = [v for _, args in ops for v in args[1::2]]
    if not xs or max(xs) <= min(xs) or max(ys) <= min(ys):
        return None
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def read_tikz(text: str) -> Document:
    """Read the ``\\draw``, ``\\fill``, ``\\filldraw`` and ``\\path`` commands of TikZ source as paths.

    Parameters
    ----------
    text : str
        LaTeX source holding a ``tikzpicture`` or bare TikZ commands.

    Returns
    -------
    Document
        The drawing in TeX points with y pointing down, sized to
        ``\\useasboundingbox`` when present and fitted to the content otherwise.

    Raises
    ------
    ValueError
        If *text* has no ``tikzpicture`` and no path commands.

    See Also
    --------
    svgwriter.export._vector._eps_read.read_eps : Read PostScript.

    Notes
    -----
    Reads what :func:`~svgwriter.export._vector._tikz.to_tikz` writes and
    common hand-written pictures. Coordinates are ``(x,y)`` and
    ``(angle:radius)``, absolute or ``+``/``++`` relative, unitless (scaled by
    the picture's ``x``, ``y``, ``scale``, ``xscale`` and ``yscale``, 1 cm by
    default) or with ``pt bp mm cm in pc`` units. Path operations are ``--``,
    ``|-``, ``-|``, ``.. controls .. and ..``, ``cycle``, ``rectangle``,
    ``circle``/``ellipse`` with ``(r)``, ``(a and b)`` or ``[radius=r]``.
    Options are colour names and xcolor mixes
    (``red!30!blue``), ``draw=``, ``fill=``, ``color=``, ``line width=`` and
    the named widths, ``opacity``, ``fill opacity``, ``draw opacity``,
    ``dashed``/``dotted``/``dash pattern=``, ``line cap``, ``line join``,
    ``miter limit`` and ``even odd rule``; colours come from
    ``\\definecolor`` (``RGB``, ``rgb``, ``HTML``, ``gray``, ``cmyk``) and
    ``\\colorlet``.

    Nodes (``\\node``, ``\\coordinate`` and ``node``/``coordinate`` inside a
    path) become centred ``<text>`` coloured by ``color``/``text``, with
    simple markup removed. A node sits ``at (x,y)``, at the current path
    point, or along the segment before it for ``pos=t``, ``midway``,
    ``near start`` and the like; ``above``, ``below``, ``left``, ``right``
    (with their pairs and an optional distance), ``anchor``, ``xshift`` and
    ``yshift`` place it. ``draw``/``fill`` with ``rectangle``, ``circle`` or
    ``ellipse`` paint a border sized from the text width, ``inner sep``
    (3.333pt) and ``minimum size/width/height``. Names such as ``(a)`` and
    ``(a.north)`` (compass anchors) are usable as path coordinates later.

    ``\\tikzset{name/.style={...}}``, ``/.append style``, ``\\tikzstyle`` and
    the picture's own ``name/.style`` define styles, expanded where the name is
    an option, with ``every node`` and ``every path``. ``scope`` options
    (colours, widths, ``shift``, ``xshift``, ``yshift``, ``scale``,
    ``xscale``, ``yscale``, ``rotate``) apply to the commands inside, nested.
    ``\\foreach \\x in {1,2,3}``, ``{0,...,4}``, ``{1,3,...,9}`` and
    ``\\x/\\y in {1/a,2/b}`` are unrolled by substituting the variables
    before parsing; arithmetic on them (``\\x*2``) is not evaluated.

    Macros, ``to``/``arc``/``grid`` operations, positioning libraries
    (``right=of a``), ``sloped``, node rotation and shading are not
    interpreted; a command that cannot be read is skipped.

    Examples
    --------
    >>> from svgwriter.export._vector._tikz_read import read_tikz
    >>> doc = read_tikz(r"\\begin{tikzpicture}\\fill[blue] (0,0) rectangle (1,1);\\end{tikzpicture}")
    >>> doc[0].get("fill"), round(doc[0].bounds().width, 2)
    ('#0000ff', 28.45)
    """
    text = _unroll(_COMMENT_RE.sub("", text))
    events = _events(text)
    if not any(kind == "cmd" for kind, *_ in events) and _PICTURE_RE.search(text) is None:
        raise ValueError("not TikZ: no tikzpicture and no \\draw, \\fill, \\filldraw or \\path command")
    picture = _picture_options(text)
    context = _Context(_definitions(text), _style_table(text, picture))
    styles = context.styles
    scopes = [_Scope(_frame(picture), _expand(_options(picture), styles))]
    every_path = _expand(styles.get("every path", []), styles)
    shapes, view = [], None
    for kind, command, options, body in events:
        if kind == "begin":
            scopes.append(scopes[-1].child(_expand(_options(options), styles)))
        elif kind == "end":
            scopes = scopes[:-1] or scopes
        else:
            pairs = scopes[-1].pairs + every_path + _expand(_options(options), styles)
            reader = _PathReader(scopes[-1].frame, context, pairs)
            try:
                ops = reader.read(_tokens(body))
            except (ValueError, IndexError, KeyError):
                continue
            if command == "useasboundingbox":
                view = _bounds(ops) or view
            elif ops:
                shapes.append(_style(command, pairs, context.colors).shape(ops))
            shapes += reader.extras
    return to_document(shapes, view)


def _plain(latex: str) -> str:
    r"""Node text without simple LaTeX markup: ``\textbf{x}`` keeps ``x``; ``\`` line breaks become spaces."""
    text = latex.replace("\\\\", " ")
    previous = None
    while previous != text:
        previous, text = text, _MARKUP_RE.sub(r"\1", text)
    return _SPACE_RE.sub(" ", text.replace("{", "").replace("}", "")).strip()
