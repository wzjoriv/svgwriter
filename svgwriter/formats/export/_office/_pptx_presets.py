"""
Outlines of common PowerPoint preset shapes (``<a:prstGeom prst=...>``) at their default proportions.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._constants import STAR_INNER_RATIO

__all__ = ["preset_points"]

Points = list[tuple[float, float]]


def _arrow(w: float, h: float, m: float) -> Points:
    """A right arrow: shaft half as thick as the box, head as long as half the shorter side."""
    head, shaft = w - m / 2, h / 4
    return [(0, shaft), (head, shaft), (head, 0), (w, h / 2), (head, h), (head, h - shaft), (0, h - shaft)]


def _turned(points: Points, w: float, h: float, turn: str) -> Points:
    """*points* of a right-pointing outline in a box turned to point left, up or down."""
    if turn == "left":
        return [(w - x, y) for x, y in points]
    if turn == "down":
        return [(y, x) for x, y in points]
    return [(y, h - x) for x, y in points]


def _vertical_arrow(w: float, h: float, m: float, turn: str) -> Points:
    return _turned(_arrow(h, w, m), w, h, turn)


def _star(w: float, h: float, points: int = 5) -> Points:
    corners = []
    for index in range(points * 2):
        angle = math.pi * index / points - math.pi / 2
        radius = 1.0 if index % 2 == 0 else STAR_INNER_RATIO
        corners.append((w / 2 + radius * w / 2 * math.cos(angle), h / 2 + radius * h / 2 * math.sin(angle)))
    return corners


_PRESETS: dict[str, Callable[[float, float, float], Points]] = {
    "triangle": lambda w, h, m: [(w / 2, 0), (w, h), (0, h)],
    "rtTriangle": lambda w, h, m: [(0, 0), (w, h), (0, h)],
    "diamond": lambda w, h, m: [(w / 2, 0), (w, h / 2), (w / 2, h), (0, h / 2)],
    "parallelogram": lambda w, h, m: [(m / 4, 0), (w, 0), (w - m / 4, h), (0, h)],
    "trapezoid": lambda w, h, m: [(m / 4, 0), (w - m / 4, 0), (w, h), (0, h)],
    "pentagon": lambda w, h, m: [(w / 2, 0), (w, 0.38 * h), (0.81 * w, h), (0.19 * w, h), (0, 0.38 * h)],
    "hexagon": lambda w, h, m: [(m / 4, 0), (w - m / 4, 0), (w, h / 2), (w - m / 4, h), (m / 4, h), (0, h / 2)],
    "homePlate": lambda w, h, m: [(0, 0), (w - m / 2, 0), (w, h / 2), (w - m / 2, h), (0, h)],
    "chevron": lambda w, h, m: [(0, 0), (w - m / 2, 0), (w, h / 2), (w - m / 2, h), (0, h), (m / 2, h / 2)],
    "rightArrow": _arrow,
    "leftArrow": lambda w, h, m: _turned(_arrow(w, h, m), w, h, "left"),
    "upArrow": lambda w, h, m: _vertical_arrow(w, h, m, "up"),
    "downArrow": lambda w, h, m: _vertical_arrow(w, h, m, "down"),
    "star5": lambda w, h, m: _star(w, h),
    "plus": lambda w, h, m: [(m / 4, 0), (w - m / 4, 0), (w - m / 4, m / 4), (w, m / 4), (w, h - m / 4),
                             (w - m / 4, h - m / 4), (w - m / 4, h), (m / 4, h), (m / 4, h - m / 4), (0, h - m / 4),
                             (0, m / 4), (m / 4, m / 4)],
}


def preset_points(name: str, left: float, top: float, width: float, height: float) -> Points | None:
    """The corners of preset *name* in a box, or None when it is not one of the supported presets.

    Examples
    --------
    >>> preset_points("diamond", 0, 0, 10, 4)
    [(5.0, 0.0), (10.0, 2.0), (5.0, 4.0), (0.0, 2.0)]
    >>> preset_points("cloud", 0, 0, 10, 4) is None
    True
    """
    outline = _PRESETS.get(name)
    if outline is None:
        return None
    return [(left + float(x), top + float(y)) for x, y in outline(width, height, min(width, height))]
