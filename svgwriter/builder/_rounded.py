"""
Closed outlines with circular fillets at chosen corners.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from ..model.elements.shapes import Path
from ..model.pathdata.builder import PathBuilder
from ._constants import ROUNDING_EPSILON

__all__ = ["rounded_outline"]

Vertex = tuple[float, float]


def _unit(a: Vertex, b: Vertex) -> tuple[float, float, float]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    return dx / length, dy / length, length


def _step(builder: PathBuilder, index: int, point: Vertex) -> None:
    if index:
        builder.line_to(*point)
    else:
        builder.move_to(*point)


def rounded_outline(points: Sequence[Vertex], radii: Sequence[float], **kwargs: Any) -> Path:
    """Build a closed path through *points* with a circular fillet at each corner.

    A fillet shrinks when its neighbours are too close for the requested radius, so the outline
    never overlaps itself. Corners with radius zero stay sharp.

    Parameters
    ----------
    points : sequence of (float, float)
        Vertices of the outline, in order.
    radii : sequence of float
        Fillet radius for each vertex.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Path`.

    Returns
    -------
    Path
        The closed outline.

    Examples
    --------
    >>> from svgwriter.builder._rounded import rounded_outline
    >>> rounded_outline([(0, 0), (10, 0), (10, 10), (0, 10)], [2] * 4).bbox.width
    10.0
    """
    count = len(points)
    cuts: list[tuple[Vertex, Vertex, float, bool] | None] = []
    for index, point in enumerate(points):
        before, after = points[index - 1], points[(index + 1) % count]
        ux, uy, back = _unit(point, before)
        vx, vy, front = _unit(point, after)
        cosine = max(-1.0, min(1.0, ux * vx + uy * vy))
        half = math.acos(cosine) / 2
        if radii[index] <= 0 or half < ROUNDING_EPSILON or half > math.pi / 2 - ROUNDING_EPSILON:
            cuts.append(None)
            continue
        reach = radii[index] / math.tan(half)
        room_back = back if radii[index - 1] <= 0 else back / 2
        room_front = front if radii[(index + 1) % count] <= 0 else front / 2
        reach = min(reach, room_back, room_front)
        sweep = (point[0] - before[0]) * (after[1] - point[1]) - (point[1] - before[1]) * (after[0] - point[0]) > 0
        entry = (point[0] + ux * reach, point[1] + uy * reach)
        exit_ = (point[0] + vx * reach, point[1] + vy * reach)
        cuts.append((entry, exit_, reach * math.tan(half), sweep))
    builder = PathBuilder()
    for index, point in enumerate(points):
        cut = cuts[index]
        if cut is None:
            _step(builder, index, point)
            continue
        entry, exit_, radius, sweep = cut
        _step(builder, index, entry)
        builder.arc_to(radius, radius, 0, False, sweep, *exit_)
    builder.close()
    return Path(builder, **kwargs)
