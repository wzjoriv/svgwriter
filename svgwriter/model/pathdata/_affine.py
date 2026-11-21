"""
Baking an affine matrix into path commands.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator

from ..transform.matrix import Matrix
from .commands import ArcTo, ClosePath, CurveTo, LineTo, MoveTo, PathCommand, QuadTo

__all__ = ["transform_arc", "transform_commands"]


def transform_arc(arc: ArcTo, matrix: Matrix) -> ArcTo:
    """Map an absolute arc through a matrix, keeping it an exact ellipse.

    The transformed ellipse's radii and rotation are recovered from the
    mapped axes; the sweep flag flips when the matrix reverses orientation.

    Parameters
    ----------
    arc : ArcTo
        An absolute arc command.
    matrix : Matrix
        The affine transform to apply.

    Returns
    -------
    ArcTo
        The transformed absolute arc.

    Examples
    --------
    >>> from svgwriter.model.pathdata import ArcTo
    >>> from svgwriter.model.pathdata._affine import transform_arc
    >>> from svgwriter.model.transform import Matrix
    >>> str(transform_arc(ArcTo(5, 5, 0, False, True, 10, 0), Matrix.scale(2)))
    'A10 10 0 0 1 20 0'
    """
    end = matrix.apply(arc.x, arc.y)
    phi = math.radians(arc.rotation)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    n11 = (matrix.a * cos_phi + matrix.c * sin_phi) * arc.rx
    n21 = (matrix.b * cos_phi + matrix.d * sin_phi) * arc.rx
    n12 = (-matrix.a * sin_phi + matrix.c * cos_phi) * arc.ry
    n22 = (-matrix.b * sin_phi + matrix.d * cos_phi) * arc.ry
    p = n11 * n11 + n12 * n12
    q = n11 * n21 + n12 * n22
    r = n21 * n21 + n22 * n22
    mean, spread = (p + r) / 2.0, math.hypot((p - r) / 2.0, q)
    rx, ry = math.sqrt(mean + spread), math.sqrt(max(mean - spread, 0.0))
    rotation = math.degrees(0.5 * math.atan2(2.0 * q, p - r))
    sweep = arc.sweep if matrix.determinant >= 0 else not arc.sweep
    return ArcTo(rx, ry, rotation, arc.large_arc, sweep, end.x, end.y)


def transform_commands(commands: Iterable[PathCommand], matrix: Matrix) -> Iterator[PathCommand]:
    """Map normalized commands through a matrix.

    Parameters
    ----------
    commands : iterable of PathCommand
        Absolute ``M``, ``L``, ``C``, ``Q``, ``A`` and ``Z`` commands, as from `PathData.normalized`.
    matrix : Matrix
        The affine transform to apply.

    Yields
    ------
    PathCommand
        The transformed commands.

    Raises
    ------
    TypeError
        If a command other than the normalized set is given.

    Examples
    --------
    >>> from svgwriter.model.pathdata import LineTo, MoveTo
    >>> from svgwriter.model.pathdata._affine import transform_commands
    >>> from svgwriter.model.transform import Matrix
    >>> [str(c) for c in transform_commands([MoveTo(0, 0), LineTo(1, 1)], Matrix.translate(5, 0))]
    ['M5 0', 'L6 1']
    """
    for command in commands:
        if isinstance(command, (MoveTo, LineTo)):
            yield type(command)(*matrix.apply(command.x, command.y))
        elif isinstance(command, CurveTo):
            yield CurveTo(
                *matrix.apply(command.x1, command.y1),
                *matrix.apply(command.x2, command.y2),
                *matrix.apply(command.x, command.y),
            )
        elif isinstance(command, QuadTo):
            yield QuadTo(*matrix.apply(command.x1, command.y1), *matrix.apply(command.x, command.y))
        elif isinstance(command, ArcTo):
            yield transform_arc(command, matrix)
        elif isinstance(command, ClosePath):
            yield command
        else:
            raise TypeError(f"expected normalized commands, got {type(command).__name__}")
