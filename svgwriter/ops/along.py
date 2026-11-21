"""
Walking along an outline: evenly spaced samples and shapes distributed along a path.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, TypeVar

import skia

from ..model.transform.matrix import Point
from ._constants import MEASURE_PRECISION
from ._skia import Geometry
from .measure import _lengths, _skia_path

if TYPE_CHECKING:
    from ..model.elements import Transformable

__all__ = ["distribute", "frames", "sample"]

T = TypeVar("T", bound="Transformable")


def frames(item: Geometry, count: int) -> list[tuple[Point, Point]]:
    """Positions and unit tangents at *count* evenly spaced distances along the outline.

    An outline whose subpaths are all closed is split into *count* equal
    steps that do not repeat the start; an open one includes both ends.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline to walk.
    count : int
        How many places; at least 1.

    Returns
    -------
    list of (Point, Point)
        Each position with the direction of travel there.

    Raises
    ------
    ValueError
        If *count* is below 1 or the outline has zero length.

    See Also
    --------
    sample : Just the positions.

    Examples
    --------
    >>> from svgwriter.ops import frames
    >>> frames("M0 0 L10 0", 2)[1]
    (Point(x=10.0, y=0.0), Point(x=1.0, y=0.0))
    """
    if count < 1:
        raise ValueError(f"need at least one place, got {count}")
    path = _skia_path(item)
    lengths = _lengths(path)
    total = sum(lengths)
    if not total:
        raise ValueError("the outline has zero length")
    measure = skia.PathMeasure(path, False, MEASURE_PRECISION)
    closed = []
    while True:
        closed.append(measure.isClosed())
        if not measure.nextContour():
            break
    steps = count if all(closed) else max(count - 1, 1)
    result = []
    measure = skia.PathMeasure(path, False, MEASURE_PRECISION)
    contour, walked = 0, 0.0
    for step in range(count):
        distance = total * step / steps
        while contour < len(lengths) - 1 and distance > walked + lengths[contour]:
            walked += lengths[contour]
            contour += 1
            measure.nextContour()
        point, tangent = measure.getPosTan(min(max(distance - walked, 0.0), lengths[contour]))
        result.append((Point(point.x(), point.y()), Point(tangent.x(), tangent.y())))
    return result


def sample(item: Geometry, count: int) -> list[Point]:
    """*count* points evenly spaced by distance along the outline.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline to walk.
    count : int
        How many points; at least 1.

    Returns
    -------
    list of Point
        The points in drawing order; see `frames` for how closed outlines are split.

    Raises
    ------
    ValueError
        If *count* is below 1 or the outline has zero length.

    Examples
    --------
    >>> from svgwriter.ops import sample
    >>> sample("M0 0 L10 0", 3)
    [Point(x=0.0, y=0.0), Point(x=5.0, y=0.0), Point(x=10.0, y=0.0)]
    >>> len(sample("M0 0 H10 V10 H0 Z", 4))
    4
    """
    return [point for point, _ in frames(item, count)]


def distribute(shapes: Sequence[T], along: Geometry, *, orient: bool = True) -> list[T]:
    """Move shapes to evenly spaced places along a path.

    Each shape's anchor (its centre unless set otherwise) lands on its place;
    places are spaced as in `sample`. The shapes are moved in place.

    Parameters
    ----------
    shapes : sequence of elements
        The shapes, in the order they go along the path.
    along : shape, text, PathData or str
        The path to follow.
    orient : bool, optional
        Also turn each shape so its +x axis follows the path. Defaults to True.

    Returns
    -------
    list
        The same shapes.

    Raises
    ------
    ValueError
        If the path has zero length.

    Examples
    --------
    >>> import svgwriter as svg
    >>> dots = svg.distribute([svg.circle(0, 0, 1) for _ in range(3)], along=svg.line(0, 0, 10, 0))
    >>> [dot.position.x for dot in dots]
    [0.0, 5.0, 10.0]
    """
    if not shapes:
        return []
    for shape, (point, tangent) in zip(shapes, frames(along, len(shapes)), strict=True):
        shape.place(point.x, point.y)
        heading = math.degrees(math.atan2(tangent.y, tangent.x))
        if orient and heading:
            shape.rotate(heading, about=(point.x, point.y))
    return list(shapes)
