"""
Walking, normalizing, sampling and node editing of path data.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from typing import TYPE_CHECKING, Final

import numpy as np

from ..transform.matrix import Matrix, Point
from ..transform.transform import TransformLike, as_transform
from ._affine import transform_commands
from ._constants import ARC_SAMPLES, CURVE_SAMPLES
from .arc import endpoint_to_center
from .commands import (
    ArcTo,
    ClosePath,
    CurveTo,
    HLineTo,
    LineTo,
    MoveTo,
    PathCommand,
    QuadTo,
    SmoothCurveTo,
    SmoothQuadTo,
    VLineTo,
)

if TYPE_CHECKING:
    from .data import PathData

__all__ = ["PathGeometry"]

ORIGIN: Final = Point(0.0, 0.0)


def _cubic(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    u = 1.0 - t
    return Point(
        u**3 * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t**3 * p3.x,
        u**3 * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t**3 * p3.y,
    )


def _quadratic(p0: Point, p1: Point, p2: Point, t: float) -> Point:
    u = 1.0 - t
    return Point(
        u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x,
        u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y,
    )


def _pairs(command: PathCommand) -> list[tuple[str, str]]:
    names = command.coordinates
    return [(names[i], names[i + 1]) for i in range(0, len(names), 2)] if len(names) % 2 == 0 else []


def _reflect(control: Point, about: Point) -> Point:
    return Point(2 * about.x - control.x, 2 * about.y - control.y)


class PathGeometry:
    """Absolute walking, normalization, sampling and node editing for :class:`~svgwriter.model.pathdata.PathData`."""

    _commands: tuple[PathCommand, ...]

    def transformed(self, transform: TransformLike) -> PathData:
        """Bake a transform into the coordinates.

        The data is normalized first, so the result uses only absolute
        ``M``, ``L``, ``C``, ``Q``, ``A`` and ``Z``; arcs stay exact arcs.

        Parameters
        ----------
        transform : Matrix or Transform or str
            The transform to apply; text is parsed as an SVG transform list.

        Returns
        -------
        PathData
            New path data with the transform applied.

        See Also
        --------
        normalized : The simplification step used first.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathData
        >>> str(PathData("M0 0 h10").transformed("translate(5 5)"))
        'M5 5 L15 5'
        """
        from .data import PathData

        matrix = transform if isinstance(transform, Matrix) else as_transform(transform).to_matrix()
        return PathData(transform_commands(self.normalized(), matrix))

    def subpaths(self) -> list[PathData]:
        """Split at each ``moveto``.

        Every piece is made absolute, so each can be used on its own.

        Returns
        -------
        list of PathData
            One path per subpath.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathData
        >>> [str(p) for p in PathData("M0 0 h10 M20 20 h5").subpaths()]
        ['M0 0 H10', 'M20 20 H25']
        """
        from .data import PathData

        pieces: list[list[PathCommand]] = []
        for _, command in self.walk():
            if isinstance(command, MoveTo) or not pieces:
                pieces.append([])
            pieces[-1].append(command)
        return [PathData(piece) for piece in pieces]


    def walk(self) -> Iterator[tuple[Point, PathCommand]]:
        """Iterate the commands in absolute form with the pen position before each.

        Yields
        ------
        tuple of (Point, PathCommand)
            The current point before the command, and the command made absolute.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathData
        >>> [(tuple(p), str(c)) for p, c in PathData("M1 1 h2").walk()]
        [((0.0, 0.0), 'M1 1'), ((1.0, 1.0), 'H3')]
        """
        current = start = ORIGIN
        for command in self._commands:
            absolute = command.to_absolute(current)
            yield current, absolute
            current = absolute.end_point(current, start)
            if isinstance(absolute, MoveTo):
                start = current
            elif isinstance(absolute, ClosePath):
                current = start

    def _editable(self) -> list[PathCommand]:
        """Absolute commands with ``H``/``V`` widened to ``L`` so every node has x and y."""
        commands: list[PathCommand] = []
        for current, command in self.walk():
            if isinstance(command, HLineTo):
                command = LineTo(command.x, current.y)
            elif isinstance(command, VLineTo):
                command = LineTo(current.x, command.y)
            commands.append(command)
        return commands

    def nodes(self) -> np.ndarray:
        """Every coordinate pair (end points and control points) as an ``(N, 2)`` array.

        Coordinates are absolute; ``H``/``V`` count as points on their line.
        Arc radii and flags are not nodes.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(N, 2)``.

        See Also
        --------
        with_nodes : Rebuild the path from edited nodes.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathData
        >>> PathData("M0 0 h10 Q15 5 10 10").nodes().tolist()
        [[0.0, 0.0], [10.0, 0.0], [15.0, 5.0], [10.0, 10.0]]
        """
        pairs = [
            (getattr(c, x), getattr(c, y))
            for c in self._editable()
            for x, y in _pairs(c)
        ]
        return np.array(pairs, dtype=float).reshape(-1, 2)

    def with_nodes(self, nodes: object) -> PathData:
        """Return the same commands with coordinates taken from an ``(N, 2)`` array.

        The commands are made absolute and ``H``/``V`` become ``L`` so every
        node has both coordinates.

        Parameters
        ----------
        nodes : array_like
            New coordinates, in the order and shape returned by `nodes`.

        Returns
        -------
        PathData
            Path data with the new coordinates.

        Raises
        ------
        ValueError
            If the array's shape does not match the path's node count.

        See Also
        --------
        nodes : The coordinate array this method consumes.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathData
        >>> d = PathData("M0 0 L10 0")
        >>> str(d.with_nodes(d.nodes() + 1))
        'M1 1 L11 1'
        """
        from .data import PathData

        commands = self._editable()
        array = np.asarray(nodes, dtype=float)
        count = sum(len(_pairs(c)) for c in commands)
        if array.shape != (count, 2):
            raise ValueError(f"expected nodes of shape ({count}, 2), got {array.shape}")
        values = iter(array.tolist())
        rebuilt = []
        for command in commands:
            changes = {}
            for x, y in _pairs(command):
                changes[x], changes[y] = next(values)
            rebuilt.append(replace(command, **changes) if changes else command)
        return PathData(rebuilt)

    def to_absolute(self) -> PathData:
        """Return the path with every command in absolute form.

        Returns
        -------
        PathData
            Equivalent path data using only uppercase commands.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathData
        >>> str(PathData("M1 1 l2 2").to_absolute())
        'M1 1 L3 3'
        """
        from .data import PathData

        return PathData(command for _, command in self.walk())

    def normalized(self) -> PathData:
        """Return absolute commands using only ``M``, ``L``, ``C``, ``Q``, ``A`` and ``Z``.

        ``H`` and ``V`` become ``L``, and smooth curves get their reflected
        control point written out.

        Returns
        -------
        PathData
            Normalized path data.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathData
        >>> str(PathData("M0 0 h10 v5").normalized())
        'M0 0 L10 0 L10 5'
        """
        from .data import PathData

        result: list[PathCommand] = []
        previous: PathCommand | None = None
        last_control: Point | None = None
        for current, command in self.walk():
            if isinstance(command, HLineTo):
                command = LineTo(command.x, current.y)
            elif isinstance(command, VLineTo):
                command = LineTo(current.x, command.y)
            elif isinstance(command, SmoothCurveTo):
                c1 = _reflect(last_control, current) if isinstance(previous, CurveTo) and last_control else current
                command = CurveTo(c1.x, c1.y, command.x2, command.y2, command.x, command.y)
            elif isinstance(command, SmoothQuadTo):
                c1 = _reflect(last_control, current) if isinstance(previous, QuadTo) and last_control else current
                command = QuadTo(c1.x, c1.y, command.x, command.y)
            if isinstance(command, CurveTo):
                last_control = Point(command.x2, command.y2)
            elif isinstance(command, QuadTo):
                last_control = Point(command.x1, command.y1)
            else:
                last_control = None
            result.append(command)
            previous = command
        return PathData(result)

    def points(self) -> Iterator[Point]:
        """Iterate points sampled along the path's outline.

        Curves and arcs are sampled at fixed resolution; lines contribute their end points.

        Yields
        ------
        Point
            Successive outline points.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathData
        >>> [tuple(p) for p in PathData("M0 0 L1 1").points()]
        [(0.0, 0.0), (1.0, 1.0)]
        """
        current = start = ORIGIN
        for command in self.normalized():
            if isinstance(command, ClosePath):
                current = start
                continue
            if isinstance(command, MoveTo):
                start = Point(command.x, command.y)
            if isinstance(command, (MoveTo, LineTo)):
                yield Point(command.x, command.y)
            elif isinstance(command, CurveTo):
                c1, c2, end = Point(command.x1, command.y1), Point(command.x2, command.y2), Point(command.x, command.y)
                for i in range(1, CURVE_SAMPLES + 1):
                    yield _cubic(current, c1, c2, end, i / CURVE_SAMPLES)
            elif isinstance(command, QuadTo):
                c1, end = Point(command.x1, command.y1), Point(command.x, command.y)
                for i in range(1, CURVE_SAMPLES + 1):
                    yield _quadratic(current, c1, end, i / CURVE_SAMPLES)
            elif isinstance(command, ArcTo):
                end = Point(command.x, command.y)
                arc = endpoint_to_center(current, end, command.rx, command.ry, command.rotation, command.large_arc, command.sweep)
                yield from (arc.sample(ARC_SAMPLES) if arc else [end])
            current = Point(command.x, command.y)  # type: ignore[attr-defined]
