"""
Fill and stroke paints resolved for flattened items: solid colours and gradient shadings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._constants import NONE, PERCENT
from ._tree import resolve

if TYPE_CHECKING:
    from ..color.color import Color
    from ..elements.core import Element
    from ..transform.matrix import Matrix

__all__ = ["Shading"]


def _paint(element: Element, name: str, default: str, rules: list) -> Color | None:
    from ..attributes.cascade import computed
    from ..color.color import Color, as_color

    value = computed(element, name, default, rules)
    text = str(value.svg_value() if hasattr(value, "svg_value") else value).strip()
    if text == NONE:
        return None
    if text == "currentColor":
        text = str(computed(element, "color", "black", rules))
    if text.startswith("url("):
        server = resolve(element, value)
        stops = _stops(server, rules) if server is not None else []
        fallback = text.split(")", 1)[1].strip()
        if stops:
            return _mean_color(stops)
        return as_color(fallback) if fallback and fallback != NONE else None
    try:
        return as_color(value if isinstance(value, Color) else text)
    except (TypeError, ValueError):
        return None


def _stops(server: Element, rules: list) -> list[tuple[float, Color]]:
    """The ``(offset, colour)`` stops of a gradient, offsets clamped to ``0..1``."""
    from ..attributes.cascade import computed
    from ..attributes.length import Length
    from ..color.color import as_color

    return [(min(max(float(Length.parse(stop.get("offset", 0)).value) / (PERCENT if "%" in str(stop.get("offset", ""))
             else 1.0), 0.0), 1.0), as_color(str(computed(stop, "stop-color", "black", rules))))
            for stop in server.iter("stop")]


def _mean_color(stops: list[tuple[float, Color]]) -> Color:
    """The average colour along a gradient's axis: the solid colour that stands in for it."""
    from ..color.color import Color

    offsets = [offset for offset, _ in stops]
    for index in range(1, len(offsets)):
        offsets[index] = max(offsets[index], offsets[index - 1])
    colors = [color.rgb for _, color in stops]
    total = [offsets[0] * channel + (1.0 - offsets[-1]) * last for channel, last in zip(colors[0], colors[-1], strict=True)]
    for (start, low), (end, high) in zip(zip(offsets, colors, strict=True), zip(offsets[1:], colors[1:], strict=True),
                                         strict=False):
        total = [sum_ + (end - start) * (a + b) / 2 for sum_, a, b in zip(total, low, high, strict=True)]
    return Color(*total)


@dataclass
class Shading:
    """A gradient fill in gradient space plus the matrix that maps it to the page.

    Attributes
    ----------
    kind : {"axial", "radial"}
        Linear or radial gradient.
    coords : tuple of float
        ``(x1, y1, x2, y2)`` for axial, ``(fx, fy, 0, cx, cy, r)`` for radial, in gradient space.
    stops : list of (float, Color)
        Offsets in ``0..1`` with their colors (stop opacity folded into nothing; PostScript has none).
    matrix : Matrix
        Gradient space to page coordinates (bounding-box units, ``gradientTransform`` and the element's
        transforms included).
    """

    kind: str
    coords: tuple[float, ...]
    stops: list[tuple[float, Color]]
    matrix: Matrix


def _shading(element: Element, to_page: Matrix, rules: list) -> Shading | None:
    """The gradient behind ``fill``, when it is a linear or radial gradient with stops."""
    from ..attributes.cascade import computed
    from ..attributes.length import Length
    from ..transform.matrix import Matrix

    value = computed(element, "fill", "black", rules)
    if not str(getattr(value, "svg_value", lambda: value)()).startswith("url("):
        return None
    server = resolve(element, value)
    if server is None or server.tag not in ("linearGradient", "radialGradient"):
        return None
    stops = _stops(server, rules)
    if not stops:
        return None
    matrix = to_page
    if str(server.get("gradientUnits", "objectBoundingBox")) != "userSpaceOnUse":
        box = element.local_bbox()  # type: ignore[attr-defined]
        if box is None or not box.width or not box.height:
            return None
        matrix = matrix @ Matrix(box.width, 0, 0, box.height, box.x, box.y)
    transform = getattr(server, "t", None)
    if transform is not None:
        matrix = matrix @ transform

    def number(name: str, default: float) -> float:
        raw = server.get(name)
        if raw is None:
            return default
        length = Length.parse(raw)
        return length.value / PERCENT if length.unit.value == "%" else length.value

    if server.tag == "linearGradient":
        coords: tuple[float, ...] = (number("x1", 0.0), number("y1", 0.0), number("x2", 1.0), number("y2", 0.0))
        return Shading("axial", coords, stops, matrix)
    cx, cy, r = number("cx", 0.5), number("cy", 0.5), number("r", 0.5)
    return Shading("radial", (number("fx", cx), number("fy", cy), 0.0, cx, cy, r), stops, matrix)
