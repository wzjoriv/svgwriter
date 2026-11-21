"""
Fluent construction of path data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._internal._registry import chainable
from ..transform.matrix import Point
from ._builder_curves import CurveCommands
from ._builder_shapes import ShapeCommands
from .commands import (
    ClosePath,
    HLineTo,
    LineTo,
    MoveTo,
    PathCommand,
    VLineTo,
)
from .data import PathData

if TYPE_CHECKING:
    from ..elements.shapes import Path

__all__ = ["PathBuilder"]


class PathBuilder(CurveCommands, ShapeCommands):
    """Accumulate path commands with chained method calls.

    Every drawing method returns the builder and accepts ``relative=True`` to
    emit the lowercase form of the command. The builder tracks the current
    point, so relative commands and closing behave as in SVG.

    Parameters
    ----------
    start : tuple of float, optional
        If given, a ``moveto`` to this point is issued immediately. Defaults to None.

    See Also
    --------
    PathData : The immutable result of `build`.

    Examples
    --------
    >>> from svgwriter.model.pathdata import PathBuilder
    >>> d = PathBuilder().move_to(0, 0).line_to(10, 0).arc_to(5, 5, 0, False, True, 10, 10).close()
    >>> str(d.build())
    'M0 0 L10 0 A5 5 0 0 1 10 10 Z'
    """

    __slots__ = ("_commands", "_current", "_start")

    def __init__(self, start: tuple[float, float] | None = None) -> None:
        self._commands: list[PathCommand] = []
        self._current = Point(0.0, 0.0)
        self._start = self._current
        if start is not None:
            self.move_to(*start)

    @property
    def current_point(self) -> Point:
        """The pen position after the most recent command.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> PathBuilder((1, 2)).line_to(5, 5, relative=True).current_point
        Point(x=6, y=7)
        """
        return self._current

    def _push(self, command: PathCommand) -> None:
        self._commands.append(command)
        self._current = command.end_point(self._current, self._start)
        if isinstance(command, MoveTo):
            self._start = self._current

    @chainable
    def move_to(self, x: float, y: float, *, relative: bool = False) -> None:
        """Start a new subpath at a point.

        Lifts the pen and moves it without drawing.

        Parameters
        ----------
        x, y : float
            Target coordinates.
        relative : bool, optional
            Emit the lowercase (relative) form of the command. Defaults to False.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        line_to : Draw to a point instead of moving.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(1, 2))
        'M1 2'
        """
        self._push(MoveTo(x, y, relative=relative))

    @chainable
    def line_to(self, x: float, y: float, *, relative: bool = False) -> None:
        """Draw a straight line to a point.

        Appends an ``L`` (or ``l``) command.

        Parameters
        ----------
        x, y : float
            End point of the line.
        relative : bool, optional
            Emit the lowercase (relative) form of the command. Defaults to False.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        horizontal_to : Axis-aligned line along x.
        vertical_to : Axis-aligned line along y.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).line_to(10, 5))
        'M0 0 L10 5'
        """
        self._push(LineTo(x, y, relative=relative))

    @chainable
    def horizontal_to(self, x: float, *, relative: bool = False) -> None:
        """Draw a horizontal line.

        Appends an ``H`` (or ``h``) command; the y coordinate is unchanged.

        Parameters
        ----------
        x : float
            Target x coordinate (an offset when relative).
        relative : bool, optional
            Emit the lowercase (relative) form of the command. Defaults to False.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        line_to : Draw to an arbitrary point.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).horizontal_to(10))
        'M0 0 H10'
        """
        self._push(HLineTo(x, relative=relative))

    @chainable
    def vertical_to(self, y: float, *, relative: bool = False) -> None:
        """Draw a vertical line.

        Appends a ``V`` (or ``v``) command; the x coordinate is unchanged.

        Parameters
        ----------
        y : float
            Target y coordinate (an offset when relative).
        relative : bool, optional
            Emit the lowercase (relative) form of the command. Defaults to False.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        line_to : Draw to an arbitrary point.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).vertical_to(10, relative=True))
        'M0 0 v10'
        """
        self._push(VLineTo(y, relative=relative))

    @chainable
    def close(self) -> None:
        """Close the current subpath.

        Appends a ``Z`` command and returns the pen to the subpath's start.


        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).line_to(5, 0).close())
        'M0 0 L5 0 Z'
        """
        self._push(ClosePath())

    def build(self) -> PathData:
        """Return the accumulated commands as immutable path data.

        Returns
        -------
        PathData
            A snapshot; later builder calls do not affect it.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> PathBuilder().move_to(0, 0).horizontal_to(5).build()
        PathData('M0 0 H5')
        """
        return PathData(self._commands)

    def to_element(self, **kwargs: Any) -> Path:
        """Wrap the data in a ``<path>`` element.

        Parameters
        ----------
        **kwargs
            Passed to `svgwriter.model.elements.shapes.Path` (attributes such as ``fill``).

        Returns
        -------
        Path
            A path element holding the built data.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).to_element(fill="red"))
        '<path d="M0 0" fill="red"/>'
        """
        from ..elements.shapes import Path

        return Path(self.build(), **kwargs)

    def __len__(self) -> int:
        return len(self._commands)

    def __str__(self) -> str:
        return str(self.build())
