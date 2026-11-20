"""
Curve and arc commands of the path builder.
"""

from __future__ import annotations

from .._internal._registry import chainable
from .commands import ArcTo, CurveTo, QuadTo, SmoothCurveTo, SmoothQuadTo

__all__ = ["CurveCommands"]


class CurveCommands:
    """Bezier and arc segments of :class:`~svgwriter.pathdata.PathBuilder`."""

    __slots__ = ()

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
