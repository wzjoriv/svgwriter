"""
Outlines of common PowerPoint preset shapes (``<a:prstGeom prst=...>``) at their default proportions.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._constants import STAR_INNER_RATIO

__all__ = ["preset_points"]

Points = list[tuple[float, float]]


Adjust = dict[str, float]


def _value(adjust: Adjust, name: str, default: float) -> float:
    return adjust.get(name, default)


def _arrow(w: float, h: float, m: float, a: Adjust) -> Points:
    """A right arrow: shaft *adj1* of the height thick, head *adj2* of the shorter side long."""
    shaft = h * (1 - _value(a, "adj1", 0.5)) / 2
    head = w - m * _value(a, "adj2", 0.5)
    return [(0, shaft), (head, shaft), (head, 0), (w, h / 2), (head, h), (head, h - shaft), (0, h - shaft)]


def _turned(points: Points, w: float, h: float, turn: str) -> Points:
    """*points* of a right-pointing outline in a box turned to point left, up or down."""
    if turn == "left":
        return [(w - x, y) for x, y in points]
    if turn == "down":
        return [(y, x) for x, y in points]
    return [(y, h - x) for x, y in points]


def _vertical_arrow(w: float, h: float, m: float, a: Adjust, turn: str) -> Points:
    return _turned(_arrow(h, w, m, a), w, h, turn)


def _star(w: float, h: float, a: Adjust, points: int = 5) -> Points:
    inner = _value(a, "adj", STAR_INNER_RATIO / 2) * 2
    corners = []
    for index in range(points * 2):
        angle = math.pi * index / points - math.pi / 2
        radius = 1.0 if index % 2 == 0 else inner
        corners.append((w / 2 + radius * w / 2 * math.cos(angle), h / 2 + radius * h / 2 * math.sin(angle)))
    return corners


def _inset(m: float, a: Adjust, default: float) -> float:
    return m * _value(a, "adj", default)


def _plus(w: float, h: float, m: float, a: Adjust) -> Points:
    d = _inset(m, a, 0.25)
    return [(d, 0), (w - d, 0), (w - d, d), (w, d), (w, h - d), (w - d, h - d), (w - d, h), (d, h), (d, h - d),
            (0, h - d), (0, d), (d, d)]


_PRESETS: dict[str, Callable[[float, float, float, Adjust], Points]] = {
    "triangle": lambda w, h, m, a: [(w * _value(a, "adj", 0.5), 0), (w, h), (0, h)],
    "rtTriangle": lambda w, h, m, a: [(0, 0), (w, h), (0, h)],
    "diamond": lambda w, h, m, a: [(w / 2, 0), (w, h / 2), (w / 2, h), (0, h / 2)],
    "parallelogram": lambda w, h, m, a: [(_inset(m, a, 0.25), 0), (w, 0), (w - _inset(m, a, 0.25), h), (0, h)],
    "trapezoid": lambda w, h, m, a: [(_inset(m, a, 0.25), 0), (w - _inset(m, a, 0.25), 0), (w, h), (0, h)],
    "pentagon": lambda w, h, m, a: [(w / 2, 0), (w, 0.38 * h), (0.81 * w, h), (0.19 * w, h), (0, 0.38 * h)],
    "hexagon": lambda w, h, m, a: [(_inset(m, a, 0.25), 0), (w - _inset(m, a, 0.25), 0), (w, h / 2),
                                   (w - _inset(m, a, 0.25), h), (_inset(m, a, 0.25), h), (0, h / 2)],
    "homePlate": lambda w, h, m, a: [(0, 0), (w - _inset(m, a, 0.5), 0), (w, h / 2), (w - _inset(m, a, 0.5), h),
                                     (0, h)],
    "chevron": lambda w, h, m, a: [(0, 0), (w - _inset(m, a, 0.5), 0), (w, h / 2), (w - _inset(m, a, 0.5), h),
                                   (0, h), (_inset(m, a, 0.5), h / 2)],
    "rightArrow": _arrow,
    "leftArrow": lambda w, h, m, a: _turned(_arrow(w, h, m, a), w, h, "left"),
    "upArrow": lambda w, h, m, a: _vertical_arrow(w, h, m, a, "up"),
    "downArrow": lambda w, h, m, a: _vertical_arrow(w, h, m, a, "down"),
    "star5": lambda w, h, m, a: _star(w, h, a),
    "plus": _plus,
}


def preset_points(name: str, left: float, top: float, width: float, height: float,
                  adjust: Adjust | None = None) -> Points | None:
    """The corners of preset *name* in a box, or None when it is not one of the supported presets.

    *adjust* holds the shape's adjust-handle values as fractions (``{"adj": 0.25}``); missing ones take
    PowerPoint's defaults.

    Examples
    --------
    >>> preset_points("diamond", 0, 0, 10, 4)
    [(5.0, 0.0), (10.0, 2.0), (5.0, 4.0), (0.0, 2.0)]
    >>> preset_points("hexagon", 0, 0, 10, 4, {"adj": 0.5})[:2]
    [(2.0, 0.0), (8.0, 0.0)]
    >>> preset_points("cloud", 0, 0, 10, 4) is None
    True
    """
    outline = _PRESETS.get(name)
    if outline is None:
        return None
    corners = outline(width, height, min(width, height), adjust or {})
    return [(left + float(x), top + float(y)) for x, y in corners]
