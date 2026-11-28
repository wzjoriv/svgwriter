"""
Path effects baked into plain path data, so every format draws them: roughened outlines, dashes as geometry and a
shape stamped along a path.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Literal

import skia

from ..model.pathdata.data import PathData
from ._constants import STAMP_STYLES, TAPER_SAMPLES
from ._skia import Geometry, from_skia, geometry_data, to_skia

__all__ = ["StampOrient", "Widths", "dashed", "roughen", "stamp", "taper"]

Widths = float | Sequence[float] | Callable[[float], float]
"""A stroke width along a path: one number, values spread evenly from start to end, or a function of 0..1."""

StampOrient = Literal["rotate", "translate", "morph"]
"""How a stamped shape follows the path: turned with it, kept upright, or bent along it."""


def _apply(item: Geometry, effect: Any) -> PathData:
    data, evenodd = geometry_data(item)
    result = skia.Path()
    if effect is None or not effect.filterPath(result, to_skia(data, evenodd=evenodd),
                                               skia.StrokeRec(skia.StrokeRec.kHairline_InitStyle), None):
        raise ValueError("the path effect produced nothing for this outline")
    return from_skia(result)


def roughen(item: Geometry, segment: float, deviation: float, seed: int = 0) -> PathData:
    """The outline of *item* broken into *segment*-long pieces, each end moved up to *deviation* at random.

    Parameters
    ----------
    item : Element or PathData
        The outline.
    segment : float
        Length of the pieces, in user units.
    deviation : float
        Largest move of a piece's end, in user units.
    seed : int, optional
        Random seed; the same seed gives the same wobble. Defaults to 0.

    Returns
    -------
    PathData
        The roughened outline.

    Raises
    ------
    ValueError
        If *segment* is not positive.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.path_effects import roughen
    >>> data = roughen(svg.rect(0, 0, 40, 20), 4, 1, seed=3)
    >>> len(data) > 10
    True
    """
    if segment <= 0:
        raise ValueError(f"segment must be positive, got {segment}")
    return _apply(item, skia.DiscretePathEffect.Make(float(segment), float(deviation), int(seed)))


def dashed(item: Geometry, intervals: tuple[float, ...], offset: float = 0.0) -> PathData:
    """The outline of *item* cut into dashes: the on pieces as open paths, ready to stroke.

    Parameters
    ----------
    item : Element or PathData
        The outline.
    intervals : tuple of float
        Dash and gap lengths, alternating (an even count; an odd count is repeated, as in SVG).
    offset : float, optional
        Distance into the pattern where the outline starts. Defaults to 0.

    Returns
    -------
    PathData
        The dashes.

    Raises
    ------
    ValueError
        If no interval is positive.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.path_effects import dashed
    >>> [type(c).__name__ for c in dashed(svg.line(0, 0, 30, 0), (10, 5))][:4]
    ['MoveTo', 'LineTo', 'MoveTo', 'LineTo']
    """
    lengths = [float(value) for value in intervals]
    if len(lengths) % 2:
        lengths *= 2
    if not lengths or max(lengths) <= 0:
        raise ValueError("dashes need at least one positive length")
    return _apply(item, skia.DashPathEffect.Make(lengths, float(offset)))


def stamp(item: Geometry, shape: Geometry, spacing: float, *, offset: float = 0.0,
          orient: StampOrient = "rotate") -> PathData:
    """Copies of *shape* placed every *spacing* along the outline of *item*.

    Parameters
    ----------
    item : Element or PathData
        The path to follow.
    shape : Element or PathData
        What to stamp, drawn around its own origin (the origin lands on the path).
    spacing : float
        Distance between copies, in user units.
    offset : float, optional
        Distance along the path of the first copy. Defaults to 0.
    orient : {"rotate", "translate", "morph"}, optional
        Turn each copy with the path, keep it upright, or bend it along the path. Defaults to "rotate".

    Returns
    -------
    PathData
        The copies, as one path to fill.

    Raises
    ------
    ValueError
        If *spacing* is not positive or *orient* is unknown.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.path_effects import stamp
    >>> dots = stamp(svg.line(0, 0, 100, 0), svg.circle(0, 0, 2), 10)
    >>> sum(type(c).__name__ == "MoveTo" for c in dots)
    10
    """
    if spacing <= 0:
        raise ValueError(f"spacing must be positive, got {spacing}")
    if orient not in STAMP_STYLES:
        raise ValueError(f"orient must be one of {', '.join(STAMP_STYLES)}, got {orient!r}")
    data, evenodd = geometry_data(shape)
    style = getattr(skia.Path1DPathEffect, STAMP_STYLES[orient])
    return _apply(item, skia.Path1DPathEffect.Make(to_skia(data, evenodd=evenodd), float(spacing), float(offset), style))


def _width_at(widths: Widths, t: float) -> float:
    if callable(widths):
        return float(widths(t))
    if isinstance(widths, (int, float)):
        return float(widths)
    values = [float(value) for value in widths]
    if len(values) == 1:
        return values[0]
    position = t * (len(values) - 1)
    index = min(int(position), len(values) - 2)
    return values[index] + (values[index + 1] - values[index]) * (position - index)


def taper(item: Geometry, widths: Widths, *, samples: int = TAPER_SAMPLES) -> PathData:
    """The outline of a stroke along *item* whose width changes from start to end, as a shape to fill.

    Parameters
    ----------
    item : Element or PathData
        The centre line.
    widths : float, sequence of float or callable
        The width: one number, values spread evenly along the line (``(1, 8, 1)`` swells in the middle), or a
        function of the position ``0..1`` along the line.
    samples : int, optional
        Points taken along each part of the line. Defaults to 64.

    Returns
    -------
    PathData
        The closed outline, one shape per part of the line.

    Raises
    ------
    ValueError
        If *samples* is below 2.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.path_effects import taper
    >>> brush = taper(svg.line(0, 0, 100, 0), (0, 10, 0))
    >>> box = brush.bbox
    >>> round(box.width), round(box.height)
    (100, 10)
    """
    if samples < 2:
        raise ValueError(f"samples must be at least 2, got {samples}")
    data, evenodd = geometry_data(item)
    measure = skia.PathMeasure(to_skia(data, evenodd=evenodd), False)
    outline = skia.Path()
    while True:
        length = measure.getLength()
        if length > 0:
            left, right = [], []
            for step in range(samples):
                t = step / (samples - 1)
                found = measure.getPosTan(t * length)
                if not found:
                    continue
                position, tangent = found
                x, y, tx, ty = position.x(), position.y(), tangent.x(), tangent.y()
                half = _width_at(widths, t) / 2
                left.append((x - ty * half, y + tx * half))
                right.append((x + ty * half, y - tx * half))
            ring = left + right[::-1]
            if len(ring) >= 3:
                outline.moveTo(*ring[0])
                for point in ring[1:]:
                    outline.lineTo(*point)
                outline.close()
        if not measure.nextContour():
            break
    return from_skia(outline)
