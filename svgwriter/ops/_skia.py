"""
Converting paths to and from skia.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias, Union

import skia

from ..pathdata.commands import ArcTo, ClosePath, CurveTo, LineTo, MoveTo, QuadTo
from ..pathdata.data import PathData
from ._constants import CONIC_SUBDIVISION, EVENODD

if TYPE_CHECKING:
    from ..elements._behavior._geometry import PathOperand

__all__ = [
    "Geometry",
    "from_skia",
    "geometry_data",
    "to_skia",
]

Geometry: TypeAlias = Union["PathOperand", PathData, str]
"""Anything with an outline: a shape, text, path data or ``d`` text."""


def geometry_data(item: Geometry) -> tuple[PathData, bool]:
    """Path data in user units plus whether it fills even-odd.

    Parameters
    ----------
    item : shape, text, PathData or str
        Anything with an outline.

    Returns
    -------
    (PathData, bool)
        The outline (with the element's own transform applied) and whether its
        ``fill-rule`` is ``evenodd``.

    Raises
    ------
    TypeError
        If *item* has no outline.

    Examples
    --------
    >>> from svgwriter.ops._skia import geometry_data
    >>> data, evenodd = geometry_data("M0 0 L10 0 L10 10 Z")
    >>> evenodd
    False
    """
    from ..elements._behavior._geometry import PathOperand

    if isinstance(item, PathOperand):
        return item.outline(), str(item.get("fill-rule", "")) == EVENODD
    if isinstance(item, PathData):
        return item, False
    if isinstance(item, str):
        return PathData(item), False
    raise TypeError(f"expected a shape, text, PathData or path text, got {type(item).__name__}")


def to_skia(data: PathData, *, evenodd: bool = False) -> Any:
    """Build a ``skia.Path`` from path data.

    Relative commands, shorthands and arcs are normalised first, so any valid path data
    converts.

    Parameters
    ----------
    data : PathData
        The outline to convert.
    evenodd : bool, optional
        Give the path an even-odd fill type. Defaults to False.

    Returns
    -------
    skia.Path
        The equivalent skia path.

    See Also
    --------
    from_skia : The inverse conversion.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import to_skia
    >>> to_skia(svg.PathData("M0 0 L10 0 L10 10 Z")).countVerbs()
    4
    """
    path = skia.Path()
    for command in data.normalized():
        if isinstance(command, MoveTo):
            path.moveTo(command.x, command.y)
        elif isinstance(command, LineTo):
            path.lineTo(command.x, command.y)
        elif isinstance(command, CurveTo):
            path.cubicTo(command.x1, command.y1, command.x2, command.y2, command.x, command.y)
        elif isinstance(command, QuadTo):
            path.quadTo(command.x1, command.y1, command.x, command.y)
        elif isinstance(command, ArcTo):
            size = skia.Path.ArcSize.kLarge_ArcSize if command.large_arc else skia.Path.ArcSize.kSmall_ArcSize
            direction = skia.PathDirection.kCW if command.sweep else skia.PathDirection.kCCW
            path.arcTo(command.rx, command.ry, command.rotation, size, direction, command.x, command.y)
        elif isinstance(command, ClosePath):
            path.close()
    if evenodd:
        path.setFillType(skia.PathFillType.kEvenOdd)
    return path


def from_skia(path: Any) -> PathData:
    """Read a ``skia.Path`` back as absolute M/L/Q/C/Z path data.

    Even-odd results are rewritten to nonzero winding first, so the data
    fills correctly without a ``fill-rule``.

    Parameters
    ----------
    path : skia.Path
        The path to read.

    Returns
    -------
    PathData
        Absolute ``M``, ``L``, ``Q``, ``C`` and ``Z`` commands; conics become quadratics.

    See Also
    --------
    to_skia : The inverse conversion.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import from_skia, to_skia
    >>> str(from_skia(to_skia(svg.PathData("M0 0 H10 V10 Z"))))
    'M0 0 L10 0 L10 10 Z'
    """
    if path.getFillType() != skia.PathFillType.kWinding:
        path = skia.AsWinding(path) or path
    verbs = skia.Path.Verb
    commands: list[Any] = []
    iterator = skia.Path.RawIter(path)
    while True:
        verb, points = iterator.next()
        if verb == verbs.kDone_Verb:
            break
        if verb == verbs.kMove_Verb:
            commands.append(MoveTo(points[0].x(), points[0].y()))
        elif verb == verbs.kLine_Verb:
            commands.append(LineTo(points[1].x(), points[1].y()))
        elif verb == verbs.kQuad_Verb:
            commands.append(QuadTo(points[1].x(), points[1].y(), points[2].x(), points[2].y()))
        elif verb == verbs.kConic_Verb:
            quads = skia.Path.ConvertConicToQuads(points[0], points[1], points[2], iterator.conicWeight(), CONIC_SUBDIVISION)
            for index in range(1, len(quads) - 1, 2):
                control, end = quads[index], quads[index + 1]
                commands.append(QuadTo(control.x(), control.y(), end.x(), end.y()))
        elif verb == verbs.kCubic_Verb:
            c1, c2, end = points[1], points[2], points[3]
            commands.append(CurveTo(c1.x(), c1.y(), c2.x(), c2.y(), end.x(), end.y()))
        elif verb == verbs.kClose_Verb:
            commands.append(ClosePath())
    return PathData(commands)
