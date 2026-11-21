"""
TikZ colours and path options resolved into fill and stroke styles.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final

from ....model.color.color import as_color
from ._constants import (
    BLACK,
    COLORLET_RE,
    COMMAND_PAINTS,
    DASH_RE,
    DASHES,
    DEFAULT_LINE_WIDTH,
    DEFINECOLOR_RE,
    HELP_LINES_COLOR,
    LINE_WIDTHS,
    PERCENT,
    RGB_SCALE,
    SIDE_SHADING_ANGLE,
    TIKZ_CAP_NAMES,
    XCOLOR,
)
from ._reading import Shape, cmyk_to_rgb
from ._tikz_syntax import _measure

if TYPE_CHECKING:
    from ._reading import RGB
    from ._tikz_syntax import Pair

__all__ = ["COLOR_MODELS", "OPTIONS"]


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
    for name, model, spec in DEFINECOLOR_RE.findall(text):
        try:
            color = COLOR_MODELS[model.strip()](spec.strip())
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        if len(color) == len(BLACK):
            colors[name.strip()] = color
    for name, expression in COLORLET_RE.findall(text):
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
    shades: dict[str, RGB] = field(default_factory=dict)
    shading_angle: float = 0.0

    def shade(self, key: str, value: str | None, angle: float | None = None) -> None:
        """A shading colour (``top color``, ``inner color``, ...), which also turns the fill on."""
        self.shades[key] = _mix(value or "black", self.colors)
        self.fill = True
        if angle is not None:
            self.shading_angle = angle

    def paint(self, key: str, value: str | None) -> None:
        """``draw``/``fill``, bare or with a colour or ``none``."""
        enabled = value != "none"
        setattr(self, key, enabled)
        if enabled and value is not None:
            setattr(self, f"{key}_color", _mix(value, self.colors))

    def shape(self, ops: list) -> Shape:
        """A shape painting *ops* with this style."""
        paint, stand_in = _shading(self.shades, self.shading_angle) if self.shades else (None, None)
        return Shape(ops, fill=(stand_in or self.fill_color or self.color) if self.fill else None, fill_paint=paint,
                     stroke=(self.draw_color or self.color) if self.draw else None,
                     fill_opacity=self.fill_opacity, stroke_opacity=self.draw_opacity, evenodd=self.evenodd,
                     stroke_width=self.line_width, linecap=self.linecap, linejoin=self.linejoin,
                     miter_limit=self.miter_limit, dashes=self.dashes)


def _shading(shades: dict[str, RGB], angle: float) -> tuple[Any, RGB]:
    """A TikZ shading as an SVG gradient over the shape's box, with its average colour as the solid stand-in."""
    from ....model.elements.paint import LinearGradient, RadialGradient, Stop
    from ._reading import _hex

    if "inner" in shades or "outer" in shades:
        colors = [shades.get("inner", shades.get("outer", BLACK)), shades.get("outer", shades.get("inner", BLACK))]
        gradient: Any = RadialGradient(*(Stop(i, _hex(c)) for i, c in enumerate(colors)))
    else:
        top, bottom = shades.get("top", shades.get("bottom", BLACK)), shades.get("bottom", shades.get("top", BLACK))
        colors = [top, shades["middle"], bottom] if "middle" in shades else [top, bottom]
        dx, dy = math.sin(math.radians(angle)) / 2, math.cos(math.radians(angle)) / 2
        gradient = LinearGradient(*(Stop(i / (len(colors) - 1), _hex(c)) for i, c in enumerate(colors)),
                                  x1=0.5 - dx, y1=0.5 - dy, x2=0.5 + dx, y2=0.5 + dy)
    mean = tuple(sum(channel) / len(colors) for channel in zip(*colors, strict=True))
    return gradient, (mean[0], mean[1], mean[2])


def _opacity(style: _Style, value: str | None) -> None:
    """``opacity``: the same opacity for fill and stroke."""
    style.fill_opacity = style.draw_opacity = float(value or 1)


def _help_lines(style: _Style, _: str | None) -> None:
    """``help lines``: TikZ's thin grey style for grids."""
    style.color = _mix(HELP_LINES_COLOR, style.colors)
    style.line_width = LINE_WIDTHS["very thin"]


def _dash_pattern(value: str | None) -> tuple[float, ...]:
    """Dash lengths of ``on <len> off <len> ...``."""
    return tuple(_measure(v) for v in DASH_RE.findall(value or ""))


OPTIONS: Final[dict[str, Callable[[_Style, str | None], None]]] = {
    "draw": lambda s, v: s.paint("draw", v),
    "fill": lambda s, v: s.paint("fill", v),
    "color": lambda s, v: setattr(s, "color", _mix(v or "black", s.colors)),
    "text": lambda s, v: setattr(s, "text_color", _mix(v or "black", s.colors)),
    "line width": lambda s, v: setattr(s, "line_width", _measure(v or "0.4pt")),
    "opacity": _opacity,
    "fill opacity": lambda s, v: setattr(s, "fill_opacity", float(v or 1)),
    "draw opacity": lambda s, v: setattr(s, "draw_opacity", float(v or 1)),
    "line cap": lambda s, v: setattr(s, "linecap", TIKZ_CAP_NAMES[v or "butt"]),
    "line join": lambda s, v: setattr(s, "linejoin", v or "miter"),
    "miter limit": lambda s, v: setattr(s, "miter_limit", float(v or 10)),
    "even odd rule": lambda s, v: setattr(s, "evenodd", True),
    "nonzero rule": lambda s, v: setattr(s, "evenodd", False),
    "dash pattern": lambda s, v: setattr(s, "dashes", _dash_pattern(v)),
    **{f"{name} color": lambda s, v, n=name: s.shade(n, v) for name in ("top", "bottom", "middle", "inner", "outer")},
    "left color": lambda s, v: s.shade("top", v, SIDE_SHADING_ANGLE),
    "right color": lambda s, v: s.shade("bottom", v, SIDE_SHADING_ANGLE),
    "shading angle": lambda s, v: setattr(s, "shading_angle", float(v or 0)),
    "help lines": _help_lines,
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
