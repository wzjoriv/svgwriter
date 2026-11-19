"""
Reading TikZ pictures back into a document of paths.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from ...color.color import as_color
from ...transform.matrix import IDENTITY
from ._reading import BLACK, Outline, Shape, cmyk_to_rgb, to_document

if TYPE_CHECKING:
    from ...document import Document
    from ._reading import RGB

__all__ = ["read_tikz"]

Point = tuple[float, float]

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
_COMMAND_RE: Final = re.compile(r"\\(filldraw|draw|fill|path|useasboundingbox)(?![A-Za-z])")
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
    return [part.strip().strip("{}").strip() for part in parts if part.strip()]


def _options(text: str) -> list[tuple[str, str | None]]:
    """``key=value`` pairs of an option list; bare keys have the value None."""
    out = []
    for part in _split(text):
        key, _, value = part.partition("=")
        out.append((" ".join(key.split()), value.strip().strip("{}").strip() if _ else None))
    return out


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

    def vector(self, text: str) -> Point:
        """SVG offset of a coordinate ``x,y`` or ``angle:radius``."""
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
        return (abs(rx * self.x_scale * (1.0 if x_unit else self.x_unit)),
                abs(ry * self.y_scale * (1.0 if y_unit else self.y_unit)))

    def _map(self, x: float, y: float, x_unit: bool, y_unit: bool) -> Point:
        """Scale a coordinate and flip y; unitless components use the unit vectors."""
        return (x * self.x_scale * (1.0 if x_unit else self.x_unit),
                -y * self.y_scale * (1.0 if y_unit else self.y_unit))


def _frame(text: str) -> _Frame:
    """The frame set by the first ``tikzpicture`` environment's ``x``, ``y`` and scale options."""
    frame = _Frame()
    match = _PICTURE_RE.search(text)
    if match is None:
        return frame
    start = match.end() + len(text[match.end():]) - len(text[match.end():].lstrip())
    if start >= len(text) or text[start] != "[":
        return frame
    for key, value in _options(_balanced(text, start)[0]):
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


def _style(command: str, options: str, colors: dict[str, RGB]) -> _Style:
    """The style of a command: its implied paints, then each option in order."""
    fill, draw = COMMAND_PAINTS[command]
    style = _Style(fill=fill, draw=draw, colors=colors)
    for key, value in _options(options):
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


class _PathReader:
    """Turns path tokens into outline operations in SVG coordinates."""

    def __init__(self, frame: _Frame) -> None:
        self.frame = frame
        self.outline = Outline()
        self.last: Point = (0.0, 0.0)
        self.base: Point = (0.0, 0.0)
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
                i = _skip_node(tokens, i)
        return self.outline.take()

    def point(self, body: str, prefix: str | None) -> Point:
        """A path point; ``++`` moves the base of later relative points, ``+`` does not."""
        dx, dy = self.frame.vector(body)
        if prefix is None:
            self.base = (dx, dy)
            return self.base
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
        if connector is None:
            self.lifted = True
        elif connector == "rectangle":
            self.outline.rect(IDENTITY, x0, y0, x - x0, y - y0)
            self.lifted = True
        elif isinstance(connector, tuple):
            self.pen()
            self.curve(connector, point)
        else:
            self.pen()
            corner = {"|-": (x0, y), "-|": (x, y0)}.get(connector)
            if corner is not None:
                self.outline.line(IDENTITY, *corner)
            self.outline.line(IDENTITY, x, y)
        self.last = point

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
        return (self.frame.vector(body), relative), i + relative + 1

    def curve(self, connector: tuple, end: Point) -> None:
        """Cubic to *end*; a relative first control is taken from the start, a relative second from *end*."""
        controls = []
        for ((dx, dy), relative), anchor in zip(connector[1:], (self.last, end), strict=True):
            controls += [anchor[0] + dx, anchor[1] + dy] if relative else [dx, dy]
        self.outline.curve(IDENTITY, *controls, *end)

    def cycle(self, connector: str | tuple | None) -> None:
        """Close the subpath, along a curve when one is pending."""
        start = self.outline.start
        if start is None or self.lifted:
            return
        if isinstance(connector, tuple):
            self.curve(connector, start)
        self.outline.close()
        self.last, self.lifted = start, True

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


def _skip_node(tokens: list[tuple[str, str]], i: int) -> int:
    """Index after a ``node``/``coordinate``: its options, name, ``at (...)`` and ``{text}``."""
    while i < len(tokens):
        kind, body = tokens[i]
        if kind in ("opts", "coord"):
            i += 1
        elif (kind, body) == ("op", "at"):
            i += 2
        elif kind == "text":
            return i + 1
        else:
            break
    return i


def _statement(text: str, start: int) -> tuple[str, int]:
    """The path text from *start* up to the ``;`` outside brackets."""
    depth = 0
    for i in range(start, len(text)):
        char = text[i]
        depth += (char in "{[(") - (char in "}])")
        if char == ";" and depth <= 0:
            return text[start:i], i + 1
    return text[start:], len(text)


def _commands(text: str) -> list[tuple[str, str, str]]:
    """``(command, options, path)`` for each path command in *text*."""
    out = []
    for match in _COMMAND_RE.finditer(text):
        pos = match.end() + len(text[match.end():]) - len(text[match.end():].lstrip())
        options = ""
        if pos < len(text) and text[pos] == "[":
            options, pos = _balanced(text, pos)
        body, _ = _statement(text, pos)
        out.append((match.group(1), options, body))
    return out


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
    ``circle``/``ellipse`` with ``(r)``, ``(a and b)`` or ``[radius=r]``;
    nodes are skipped. Options are colour names and xcolor mixes
    (``red!30!blue``), ``draw=``, ``fill=``, ``color=``, ``line width=`` and
    the named widths, ``opacity``, ``fill opacity``, ``draw opacity``,
    ``dashed``/``dotted``/``dash pattern=``, ``line cap``, ``line join``,
    ``miter limit`` and ``even odd rule``; colours come from
    ``\\definecolor`` (``RGB``, ``rgb``, ``HTML``, ``gray``, ``cmyk``) and
    ``\\colorlet``. Macros, ``\\foreach``, scopes, styles, ``to``/``arc``/
    ``grid`` operations, node text and shading are not interpreted; a
    command that cannot be read is skipped.

    Examples
    --------
    >>> from svgwriter.export._vector._tikz_read import read_tikz
    >>> doc = read_tikz(r"\\begin{tikzpicture}\\fill[blue] (0,0) rectangle (1,1);\\end{tikzpicture}")
    >>> doc[0].get("fill"), round(doc[0].bounds().width, 2)
    ('#0000ff', 28.45)
    """
    text = _COMMENT_RE.sub("", text)
    commands = _commands(text)
    if not commands and _PICTURE_RE.search(text) is None:
        raise ValueError("not TikZ: no tikzpicture and no \\draw, \\fill, \\filldraw or \\path command")
    frame, colors = _frame(text), _definitions(text)
    shapes, view = [], None
    for command, options, body in commands:
        try:
            ops = _PathReader(frame).read(_tokens(body))
        except (ValueError, IndexError, KeyError):
            continue
        if command == "useasboundingbox":
            view = _bounds(ops) or view
        else:
            shapes.append(_style(command, options, colors).shape(ops))
    return to_document(shapes, view)
