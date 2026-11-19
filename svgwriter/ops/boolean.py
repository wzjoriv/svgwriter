"""Boolean path operations (union, intersection, difference, xor)."""

from __future__ import annotations

import enum

import skia

from ..pathdata.data import PathData
from ._skia import Geometry, from_skia, geometry_data, to_skia

__all__ = ["BooleanOp", "combine", "difference", "intersection", "simplify", "union", "xor"]


class BooleanOp(enum.Enum):
    """How :func:`combine` merges two outlines.

    ``UNION``, ``INTERSECTION``, ``DIFFERENCE``, ``REVERSE_DIFFERENCE`` (what only the
    second outline covers) and ``XOR`` map to skia's path operations.

    Examples
    --------
    >>> from svgwriter.ops import BooleanOp
    >>> BooleanOp.XOR.name
    'XOR'
    """

    UNION = "kUnion_PathOp"
    INTERSECTION = "kIntersect_PathOp"
    DIFFERENCE = "kDifference_PathOp"
    REVERSE_DIFFERENCE = "kReverseDifference_PathOp"
    XOR = "kXOR_PathOp"


def combine(first: Geometry, second: Geometry, op: BooleanOp) -> PathData:
    """Combine two outlines with a boolean operation.

    The result has no self-intersections; the named helpers :func:`union`,
    :func:`intersection`, :func:`difference` and :func:`xor` call this.

    Parameters
    ----------
    first, second : shape, text, PathData or str
        Outlines in user units; each element's own ``transform`` and
        ``fill-rule`` are honoured.
    op : BooleanOp
        The operation.

    Returns
    -------
    PathData
        The resulting outline (lines, quadratics and cubics).

    Raises
    ------
    ValueError
        If skia cannot compute the result.

    See Also
    --------
    union : Combine any number of outlines.

    Examples
    --------
    >>> from svgwriter.ops import BooleanOp, combine
    >>> str(combine("M0 0H10V10H0Z", "M5 0H15V10H5Z", BooleanOp.UNION))
    'M5 0 L0 0 L0 10 L15 10 L15 0 L5 0 Z'
    """
    a_data, a_evenodd = geometry_data(first)
    b_data, b_evenodd = geometry_data(second)
    result = skia.Op(to_skia(a_data, evenodd=a_evenodd), to_skia(b_data, evenodd=b_evenodd), getattr(skia.PathOp, op.value))
    if result is None:
        raise ValueError(f"skia could not compute the {op.name.lower()} of these outlines")
    return from_skia(result)


def union(first: Geometry, *others: Geometry) -> PathData:
    """Area covered by any of the outlines.

    With a single outline this simplifies it.

    Parameters
    ----------
    first : shape, text, PathData or str
        The first outline.
    *others : shape, text, PathData or str
        Further outlines to add.

    Returns
    -------
    PathData
        The merged outline.

    Raises
    ------
    ValueError
        If skia cannot compute the union.

    See Also
    --------
    combine : Apply any boolean operation to two outlines.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import bounds, union
    >>> merged = union(svg.Rect(0, 0, 10, 10), svg.Rect(5, 0, 10, 10))
    >>> (bounds(merged).width, bounds(merged).height)
    (15.0, 10.0)
    """
    if not others:
        return simplify(first)
    builder = skia.OpBuilder()
    for item in (first, *others):
        data, evenodd = geometry_data(item)
        builder.add(to_skia(data, evenodd=evenodd), skia.PathOp.kUnion_PathOp)
    result = builder.resolve()
    if result is None:
        raise ValueError("skia could not compute the union of these outlines")
    return from_skia(result)


def intersection(first: Geometry, second: Geometry) -> PathData:
    """Area covered by both outlines.

    Parameters
    ----------
    first, second : shape, text, PathData or str
        The outlines to intersect.

    Returns
    -------
    PathData
        The overlapping area.

    See Also
    --------
    combine : The general operation behind this function.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import bounds, intersection
    >>> overlap = intersection(svg.Rect(0, 0, 10, 10), svg.Rect(5, 0, 10, 10))
    >>> bounds(overlap).width
    5.0
    """
    return combine(first, second, BooleanOp.INTERSECTION)


def difference(first: Geometry, second: Geometry) -> PathData:
    """Area of *first* not covered by *second*.

    Parameters
    ----------
    first, second : shape, text, PathData or str
        The outline to keep and the outline to subtract.

    Returns
    -------
    PathData
        What remains of *first*.

    See Also
    --------
    combine : The general operation behind this function.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import bounds, difference
    >>> rest = difference(svg.Rect(0, 0, 10, 10), svg.Rect(5, 0, 10, 10))
    >>> bounds(rest).width
    5.0
    """
    return combine(first, second, BooleanOp.DIFFERENCE)


def xor(first: Geometry, second: Geometry) -> PathData:
    """Area covered by exactly one of the outlines.

    Parameters
    ----------
    first, second : shape, text, PathData or str
        The outlines to compare.

    Returns
    -------
    PathData
        The non-overlapping parts of both outlines.

    See Also
    --------
    combine : The general operation behind this function.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import contains, xor
    >>> both = xor(svg.Rect(0, 0, 10, 10), svg.Rect(5, 0, 10, 10))
    >>> contains(both, 2, 5), contains(both, 7, 5)
    (True, False)
    """
    return combine(first, second, BooleanOp.XOR)


def simplify(item: Geometry) -> PathData:
    """Equivalent outline with no self-intersections or overlaps.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline to clean up.

    Returns
    -------
    PathData
        An outline that fills the same area.

    Raises
    ------
    ValueError
        If skia cannot simplify the outline.

    See Also
    --------
    union : Merge several outlines.

    Examples
    --------
    >>> from svgwriter.ops import simplify
    >>> str(simplify("M0 0H10V10H0Z"))
    'M0 0 L10 0 L10 10 L0 10 Z'
    """
    data, evenodd = geometry_data(item)
    result = skia.Simplify(to_skia(data, evenodd=evenodd))
    if result is None:
        raise ValueError("skia could not simplify this outline")
    return from_skia(result)
