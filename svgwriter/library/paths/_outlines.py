"""
Outlines of parametric stars, polygons and arcs, computed the way Inkscape draws them.
"""

from __future__ import annotations

import math

from ...model.pathdata.builder import PathBuilder
from ._constants import ARC_MAX_SEGMENTS, ARC_MIN_RADIUS, ARC_TURN_PARTS, STAR_HANDLE_REACH

__all__ = ["arc_outline", "star_outline"]

Vector = tuple[float, float]


def _unit_normal(origin: Vector, other: Vector) -> Vector:
    length = math.dist(origin, other)
    return (other[1] - origin[1]) / length, (other[0] - origin[0]) / length


def star_outline(cx: float, cy: float, radii: Vector, args: Vector, sides: int, *, flatsided: bool,
                 rounded: float) -> PathBuilder:
    """The outline of a ``sodipodi:type="star"`` path (randomization is not applied)."""

    def corner(kind: int, index: int) -> Vector:
        angle = args[kind] + math.tau / sides * (index % sides)
        return cx + radii[kind] * math.cos(angle), cy + radii[kind] * math.sin(angle)

    def handle(kind: int, index: int, before: bool) -> Vector:
        index %= sides
        here = corner(kind, index)
        previous_index, next_index = (index - 1) % sides, (index + 1) % sides
        if flatsided:
            previous, following = corner(kind, previous_index), corner(kind, next_index)
        else:
            previous = corner(1 - kind, index if kind == 1 else previous_index)
            following = corner(1 - kind, index if kind == 0 else next_index)
        middle = ((previous[0] + following[0]) / 2, (previous[1] + following[1]) / 2)
        across = _unit_normal(middle, following)
        direction = _unit_normal(here, (middle[0] + STAR_HANDLE_REACH * across[0], middle[1] + STAR_HANDLE_REACH * across[1]))
        reach = rounded * (-math.dist(previous, here) if before else math.dist(following, here))
        return here[0] + reach * direction[0], here[1] + reach * direction[1]

    path = PathBuilder().move_to(*corner(0, 0))
    sharp = rounded == 0
    for index in range(sides):
        if not flatsided:
            if sharp:
                path.line_to(*corner(1, index))
            else:
                path.curve_to(*handle(0, index, False), *handle(1, index, True), *corner(1, index))
        if sharp and index < sides - 1:
            path.line_to(*corner(0, index + 1))
        elif not sharp:
            kind = 0 if flatsided else 1
            path.curve_to(*handle(kind, index, False), *handle(0, index + 1, True), *corner(0, index + 1))
    return path.close()


def arc_outline(cx: float, cy: float, rx: float, ry: float, start: float, end: float, kind: str) -> PathBuilder | None:
    """The outline of a ``sodipodi:type="arc"`` path; None when a radius is zero."""
    if abs(rx) < ARC_MIN_RADIUS or abs(ry) < ARC_MIN_RADIUS:
        return None
    sweep = end - start
    if sweep <= 0:
        sweep += math.tau
    count = min(1 + int(sweep * ARC_TURN_PARTS / math.tau), ARC_MAX_SEGMENTS)
    step = sweep / count
    path = PathBuilder().move_to(cx + rx * math.cos(start), cy + ry * math.sin(start))
    for index in range(1, count + 1):
        angle = start + index * step
        path.arc_to(rx, ry, 0, False, True, cx + rx * math.cos(angle), cy + ry * math.sin(angle))
    if not math.isclose(sweep, math.tau) and kind == "slice":
        path.line_to(cx, cy)
    if kind != "arc":
        path.close()
    return path
