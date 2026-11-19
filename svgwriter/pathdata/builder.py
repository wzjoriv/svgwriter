"""
Fluent construction of path data.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Final

from .._internal._registry import chainable
from .._internal._typing import Self
from ..transform.matrix import Point
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
from .data import PathData

if TYPE_CHECKING:
    from ..elements.shapes import Path

__all__ = ["PathBuilder"]

FULL_CIRCLE: Final = 360.0
QUARTER_TURN: Final = 90.0


class PathBuilder:
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
    >>> from svgwriter.pathdata import PathBuilder
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
        >>> from svgwriter.pathdata import PathBuilder
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
        >>> from svgwriter.pathdata import PathBuilder
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
        >>> from svgwriter.pathdata import PathBuilder
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
        >>> from svgwriter.pathdata import PathBuilder
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
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).vertical_to(10, relative=True))
        'M0 0 v10'
        """
        self._push(VLineTo(y, relative=relative))

    @chainable
    def curve_to(
        self, x1: float, y1: float, x2: float, y2: float, x: float, y: float, *, relative: bool = False
    ) -> None:
        """Draw a cubic Bezier curve.

        Appends a ``C`` (or ``c``) command with two explicit control points.

        Parameters
        ----------
        x1, y1 : float
            First control point.
        x2, y2 : float
            Second control point.
        x, y : float
            End point of the curve.
        relative : bool, optional
            Emit the lowercase (relative) form of the command. Defaults to False.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        smooth_curve_to : Cubic curve with a reflected first control point.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).curve_to(1, 1, 2, 1, 3, 0))
        'M0 0 C1 1 2 1 3 0'
        """
        self._push(CurveTo(x1, y1, x2, y2, x, y, relative=relative))

    @chainable
    def smooth_curve_to(self, x2: float, y2: float, x: float, y: float, *, relative: bool = False) -> None:
        """Draw a smooth cubic Bezier curve.

        Appends an ``S`` (or ``s``) command; the first control point is the reflection of the previous curve's second.

        Parameters
        ----------
        x2, y2 : float
            Second control point.
        x, y : float
            End point of the curve.
        relative : bool, optional
            Emit the lowercase (relative) form of the command. Defaults to False.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        curve_to : Cubic curve with explicit control points.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).curve_to(1, 1, 2, 1, 3, 0).smooth_curve_to(5, -1, 6, 0))
        'M0 0 C1 1 2 1 3 0 S5 -1 6 0'
        """
        self._push(SmoothCurveTo(x2, y2, x, y, relative=relative))

    @chainable
    def quad_to(self, x1: float, y1: float, x: float, y: float, *, relative: bool = False) -> None:
        """Draw a quadratic Bezier curve.

        Appends a ``Q`` (or ``q``) command.

        Parameters
        ----------
        x1, y1 : float
            Control point.
        x, y : float
            End point of the curve.
        relative : bool, optional
            Emit the lowercase (relative) form of the command. Defaults to False.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        smooth_quad_to : Quadratic curve with a reflected control point.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).quad_to(5, 5, 10, 0))
        'M0 0 Q5 5 10 0'
        """
        self._push(QuadTo(x1, y1, x, y, relative=relative))

    @chainable
    def smooth_quad_to(self, x: float, y: float, *, relative: bool = False) -> None:
        """Draw a smooth quadratic Bezier curve.

        Appends a ``T`` (or ``t``) command; the control point is the reflection of the previous one.

        Parameters
        ----------
        x, y : float
            End point of the curve.
        relative : bool, optional
            Emit the lowercase (relative) form of the command. Defaults to False.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        quad_to : Quadratic curve with an explicit control point.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).quad_to(5, 5, 10, 0).smooth_quad_to(20, 0))
        'M0 0 Q5 5 10 0 T20 0'
        """
        self._push(SmoothQuadTo(x, y, relative=relative))

    @chainable
    def arc_to(
        self,
        rx: float,
        ry: float,
        rotation: float,
        large_arc: bool,
        sweep: bool,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None:
        """Draw an elliptical arc.

        Appends an ``A`` (or ``a``) command; the flags choose one of the four arcs through the endpoints.

        Parameters
        ----------
        rx, ry : float
            Ellipse radii.
        rotation : float
            Rotation of the ellipse's x axis, in degrees.
        large_arc : bool
            Choose the arc spanning more than half the ellipse.
        sweep : bool
            Choose the clockwise (positive-angle) direction.
        x, y : float
            End point of the arc.
        relative : bool, optional
            Emit the lowercase (relative) form of the command. Defaults to False.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        circle : Append a full circle.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).arc_to(5, 5, 0, False, True, 10, 0))
        'M0 0 A5 5 0 0 1 10 0'
        """
        self._push(ArcTo(rx, ry, rotation, large_arc, sweep, x, y, relative=relative))

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
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).line_to(5, 0).close())
        'M0 0 L5 0 Z'
        """
        self._push(ClosePath())

    def extend(self, data: PathData | str) -> Self:
        """Append existing path data.

        Every command of `data` is pushed in order, so the current point follows it.

        Parameters
        ----------
        data : PathData or str
            Commands to append; text is parsed and must begin with a ``moveto``.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        Raises
        ------
        PathSyntaxError
            If `data` is text that is not valid path data.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).extend("M5 5 l1 1"))
        'M0 0 M5 5 l1 1'
        """
        if isinstance(data, str):
            text = data.strip()
            if text and text[0] not in "Mm":
                text = f"M{self._current.x} {self._current.y} {text}"
                for command in list(PathData(text))[1:]:
                    self._push(command)
                return self
            data = PathData(text)
        for command in data:
            self._push(command)
        return self

    def circle(self, cx: float, cy: float, r: float) -> Self:
        """Append a full circle as two half arcs.

        The subpath starts at the leftmost point and is closed.

        Parameters
        ----------
        cx, cy : float
            Centre of the circle.
        r : float
            Radius.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        regular_polygon : Append a closed polygon.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().circle(5, 5, 5))
        'M0 5 A5 5 0 0 1 10 5 A5 5 0 0 1 0 5 Z'
        """
        self.move_to(cx - r, cy)
        self.arc_to(r, r, 0, False, True, cx + r, cy)
        self.arc_to(r, r, 0, False, True, cx - r, cy)
        return self.close()

    def regular_polygon(self, cx: float, cy: float, radius: float, sides: int, rotation: float = -QUARTER_TURN) -> Self:
        """Append a closed regular polygon.

        Vertices are spaced evenly on a circle; the first vertex points up by default.

        Parameters
        ----------
        cx, cy : float
            Centre of the polygon.
        radius : float
            Distance from the centre to each vertex.
        sides : int
            Number of sides; at least 3.
        rotation : float, optional
            Angle of the first vertex in degrees, measured clockwise from the
            positive x axis. Defaults to -90 (pointing up).

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        Raises
        ------
        ValueError
            If `sides` is less than 3.

        See Also
        --------
        circle : Append a full circle.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().regular_polygon(0, 0, 10, 3))
        'M0 -10 L8.6603 5 L-8.6603 5 Z'
        """
        if sides < 3:
            raise ValueError("a polygon needs at least three sides")
        for i in range(sides):
            angle = math.radians(rotation + FULL_CIRCLE * i / sides)
            x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
            if i == 0:
                self.move_to(x, y)
            else:
                self.line_to(x, y)
        return self.close()

    def build(self) -> PathData:
        """Return the accumulated commands as immutable path data.

        Returns
        -------
        PathData
            A snapshot; later builder calls do not affect it.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> PathBuilder().move_to(0, 0).horizontal_to(5).build()
        PathData('M0 0 H5')
        """
        return PathData(self._commands)

    def to_element(self, **kwargs: Any) -> Path:
        """Wrap the data in a ``<path>`` element.

        Parameters
        ----------
        **kwargs
            Passed to `svgwriter.elements.shapes.Path` (attributes such as ``fill``).

        Returns
        -------
        Path
            A path element holding the built data.

        Examples
        --------
        >>> from svgwriter.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).to_element(fill="red"))
        '<path d="M0 0" fill="red"/>'
        """
        from ..elements.shapes import Path

        return Path(self.build(), **kwargs)

    def __len__(self) -> int:
        return len(self._commands)

    def __str__(self) -> str:
        return str(self.build())
