"""
Exact measurement, hit testing and stroking of outlines.
"""

from __future__ import annotations

from typing import Any, Final, Literal

import skia

from ..pathdata.data import BBox, PathData
from ..transform.matrix import Point
from ._skia import Geometry, from_skia, geometry_data, to_skia

__all__ = [
    "Cap",
    "Join",
    "bounds",
    "contains",
    "point_at_length",
    "stroke_to_path",
    "tangent_at_length",
    "total_length",
]

Cap = Literal["butt", "round", "square"]
Join = Literal["miter", "round", "bevel"]

DEFAULT_STROKE_WIDTH: Final = 1.0
DEFAULT_MITER_LIMIT: Final = 4.0
MEASURE_PRECISION: Final = 16.0
_CAPS: Final = {"butt": "kButt_Cap", "round": "kRound_Cap", "square": "kSquare_Cap"}
_JOINS: Final = {"miter": "kMiter_Join", "round": "kRound_Join", "bevel": "kBevel_Join"}


def _skia_path(item: Geometry) -> Any:
    data, evenodd = geometry_data(item)
    return to_skia(data, evenodd=evenodd)


def bounds(item: Geometry) -> BBox:
    """Tight bounding box computed from the curves, not from samples.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline to measure.

    Returns
    -------
    BBox
        The smallest axis-aligned box around the outline.

    Examples
    --------
    >>> from svgwriter.ops import bounds
    >>> box = bounds("M0 0 L10 20")
    >>> (box.width, box.height)
    (10.0, 20.0)
    """
    path = _skia_path(item)
    rect = path.computeTightBounds()
    return BBox(rect.left(), rect.top(), rect.width(), rect.height())


def contains(item: Geometry, x: float, y: float) -> bool:
    """Whether ``(x, y)`` is inside the filled outline (honours ``fill-rule``).

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline to test.
    x, y : float
        The point, in the outline's user units.

    Returns
    -------
    bool
        True when the point is filled.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import contains
    >>> contains(svg.Circle(50, 50, 40), 50, 50)
    True
    >>> contains(svg.Circle(50, 50, 40), 5, 5)
    False
    """
    path = _skia_path(item)
    return bool(path.contains(x, y))


def _lengths(path: Any) -> list[float]:
    measure = skia.PathMeasure(path, False, MEASURE_PRECISION)
    lengths = []
    while True:
        lengths.append(measure.getLength())
        if not measure.nextContour():
            return lengths


def total_length(item: Geometry) -> float:
    """Length of every subpath added together, like ``getTotalLength()``.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline to measure.

    Returns
    -------
    float
        Length in user units.

    See Also
    --------
    point_at_length : Find the point at a given distance.

    Examples
    --------
    >>> from svgwriter.ops import total_length
    >>> total_length("M0 0 L30 40")
    50.0
    """
    path = _skia_path(item)
    return sum(_lengths(path))


def _position(item: Geometry, distance: float, feature: str) -> tuple[Point, Point]:
    path = _skia_path(item)
    lengths = _lengths(path)
    if not any(lengths):
        raise ValueError("the outline has zero length")
    index, offset = len(lengths) - 1, lengths[-1]
    walked = 0.0
    for position, length in enumerate(lengths):
        if distance <= walked + length:
            index, offset = position, max(distance - walked, 0.0)
            break
        walked += length
    measure = skia.PathMeasure(path, False, MEASURE_PRECISION)
    for _ in range(index):
        measure.nextContour()
    point, tangent = measure.getPosTan(offset)
    return Point(point.x(), point.y()), Point(tangent.x(), tangent.y())


def point_at_length(item: Geometry, distance: float) -> Point:
    """Point *distance* along the outline, like ``getPointAtLength()``.

    Distances are clamped to ``0..total_length``.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline to walk along.
    distance : float
        Distance from the start in user units.

    Returns
    -------
    Point
        The position on the outline.

    Raises
    ------
    ValueError
        If the outline has zero length.

    See Also
    --------
    tangent_at_length : The direction at the same position.

    Examples
    --------
    >>> from svgwriter.ops import point_at_length
    >>> point_at_length("M0 0 L30 40", 25)
    Point(x=15.0, y=20.0)
    """
    return _position(item, distance, "point at length")[0]


def tangent_at_length(item: Geometry, distance: float) -> Point:
    """Unit tangent direction *distance* along the outline.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline to walk along.
    distance : float
        Distance from the start in user units; clamped to ``0..total_length``.

    Returns
    -------
    Point
        A unit vector pointing along the outline.

    Raises
    ------
    ValueError
        If the outline has zero length.

    See Also
    --------
    point_at_length : The position at the same distance.

    Examples
    --------
    >>> from svgwriter.ops import tangent_at_length
    >>> tangent_at_length("M0 0 L30 0", 5)
    Point(x=1.0, y=0.0)
    """
    return _position(item, distance, "tangent at length")[1]


def stroke_to_path(
    item: Geometry,
    width: float = DEFAULT_STROKE_WIDTH,
    *,
    cap: Cap = "butt",
    join: Join = "miter",
    miter_limit: float = DEFAULT_MITER_LIMIT,
) -> PathData:
    """The filled outline a stroke of *width* would paint.

    The result can be filled, combined with other outlines or exported in place of the stroke.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline to stroke.
    width : float, optional
        Stroke width in user units. Defaults to 1.0.
    cap : {"butt", "round", "square"}, optional
        ``stroke-linecap`` value. Defaults to "butt".
    join : {"miter", "round", "bevel"}, optional
        ``stroke-linejoin`` value. Defaults to "miter".
    miter_limit : float, optional
        ``stroke-miterlimit``. Defaults to 4.0.

    Returns
    -------
    PathData
        The outline of the stroked area.

    See Also
    --------
    bounds : Measure the resulting outline.

    Examples
    --------
    >>> from svgwriter.ops import stroke_to_path
    >>> str(stroke_to_path("M0 0 L10 0", 2))
    'M0 -1 L10 -1 L10 1 L0 1 L0 -1 Z'
    """
    path = _skia_path(item)
    paint = skia.Paint(
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=width,
        StrokeCap=getattr(skia.Paint, _CAPS[cap]),
        StrokeJoin=getattr(skia.Paint, _JOINS[join]),
        StrokeMiter=miter_limit,
    )
    result = skia.Path()
    paint.getFillPath(path, result)
    return from_skia(result)

