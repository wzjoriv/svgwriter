"""
TikZ path operations read into outlines: segments, curves, cycles, nodes and ellipses.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from ...transform.matrix import IDENTITY
from ._constants import (
    ANCHORS,
    DIAGONAL,
    FULL_TURN,
    INNER_SEP,
    NODE_BASELINE,
    NODE_FONT_SIZE,
    NODE_POSITIONS,
    NODE_SHAPES,
    NODE_TEXT_HEIGHT,
    POSITIONS,
)
from ._reading import Outline
from ._tikz_nodes import _Place, _plain, _read_node
from ._tikz_styles import _style
from ._tikz_syntax import _expand, _length, _options

if TYPE_CHECKING:
    from ._tikz_nodes import _Context
    from ._tikz_scopes import _Frame
    from ._tikz_syntax import Pair, Point

__all__: list[str] = []


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
        from ...elements.text._text import Text
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
