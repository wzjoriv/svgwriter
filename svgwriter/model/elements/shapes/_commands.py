"""
Drawing commands for ``<path>``: ``move_to``, ``line_to``, curves, arcs, ``close`` and ``build``.
"""

from __future__ import annotations

from typing import Any

from ...._internal._typing import Self
from ...pathdata.builder import PathBuilder
from ...pathdata.commands import (
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
from ...pathdata.data import PathData

__all__ = ["PathCommands"]


class PathCommands:
    """Chainable drawing commands; mixed into :class:`~svgwriter.model.elements.shapes.Path`."""

    __slots__ = ()

    def _push(self, command: PathCommand) -> Self:
        data = self.d
        if not len(data) and not isinstance(command, MoveTo):
            name = type(command).__name__
            raise ValueError(f"a path starts with move_to(x, y); {name} has no current point to start from")
        self.attributes["d"] = PathData((*data, command))
        return self

    def move_to(self, x: float, y: float, *, relative: bool = False) -> Self:
        """Start a new subpath.

        Parameters
        ----------
        x, y : float
            The new current point.
        relative : bool, optional
            Use the lowercase, relative form of the command. Defaults to False.

        Returns
        -------
        Path
            This path, for chaining.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(1, 2).d)
        'M1 2'
        """
        return self._push(MoveTo(x, y, relative=relative))

    def line_to(self, x: float, y: float, *, relative: bool = False) -> Self:
        """Draw a straight line to a point.

        Parameters
        ----------
        x, y : float
            The end point.
        relative : bool, optional
            Use the lowercase, relative form of the command. Defaults to False.

        Returns
        -------
        Path
            This path, for chaining.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(0, 0).line_to(1, 2).d)
        'M0 0 L1 2'
        """
        return self._push(LineTo(x, y, relative=relative))

    def horizontal_to(self, x: float, *, relative: bool = False) -> Self:
        """Draw a horizontal line.

        Parameters
        ----------
        x : float
            The end x coordinate.
        relative : bool, optional
            Use the lowercase, relative form of the command. Defaults to False.

        Returns
        -------
        Path
            This path, for chaining.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(0, 0).horizontal_to(5).d)
        'M0 0 H5'
        """
        return self._push(HLineTo(x, relative=relative))

    def vertical_to(self, y: float, *, relative: bool = False) -> Self:
        """Draw a vertical line.

        Parameters
        ----------
        y : float
            The end y coordinate.
        relative : bool, optional
            Use the lowercase, relative form of the command. Defaults to False.

        Returns
        -------
        Path
            This path, for chaining.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(0, 0).vertical_to(6, relative=True).d)
        'M0 0 v6'
        """
        return self._push(VLineTo(y, relative=relative))

    def curve_to(
        self, x1: float, y1: float, x2: float, y2: float, x: float, y: float, *, relative: bool = False
    ) -> Self:
        """Draw a cubic Bézier curve.

        Parameters
        ----------
        x1, y1 : float
            First control point.
        x2, y2 : float
            Second control point.
        x, y : float
            End point.
        relative : bool, optional
            Use the lowercase, relative form of the command. Defaults to False.

        Returns
        -------
        Path
            This path, for chaining.

        See Also
        --------
        smooth_curve_to : Reuse the previous control point.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(0, 0).curve_to(1, 2, 3, 4, 5, 6).d)
        'M0 0 C1 2 3 4 5 6'
        """
        return self._push(CurveTo(x1, y1, x2, y2, x, y, relative=relative))

    def smooth_curve_to(self, x2: float, y2: float, x: float, y: float, *, relative: bool = False) -> Self:
        """Draw a cubic Bézier whose first control point mirrors the previous one.

        Parameters
        ----------
        x2, y2 : float
            Second control point.
        x, y : float
            End point.
        relative : bool, optional
            Use the lowercase, relative form of the command. Defaults to False.

        Returns
        -------
        Path
            This path, for chaining.

        See Also
        --------
        curve_to : Give both control points explicitly.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(0, 0).curve_to(1, 2, 3, 4, 5, 6).smooth_curve_to(7, 8, 9, 10).d)
        'M0 0 C1 2 3 4 5 6 S7 8 9 10'
        """
        return self._push(SmoothCurveTo(x2, y2, x, y, relative=relative))

    def quad_to(self, x1: float, y1: float, x: float, y: float, *, relative: bool = False) -> Self:
        """Draw a quadratic Bézier curve.

        Parameters
        ----------
        x1, y1 : float
            Control point.
        x, y : float
            End point.
        relative : bool, optional
            Use the lowercase, relative form of the command. Defaults to False.

        Returns
        -------
        Path
            This path, for chaining.

        See Also
        --------
        smooth_quad_to : Reuse the previous control point.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(0, 0).quad_to(1, 2, 3, 4).d)
        'M0 0 Q1 2 3 4'
        """
        return self._push(QuadTo(x1, y1, x, y, relative=relative))

    def smooth_quad_to(self, x: float, y: float, *, relative: bool = False) -> Self:
        """Draw a quadratic Bézier whose control point mirrors the previous one.

        Parameters
        ----------
        x, y : float
            End point.
        relative : bool, optional
            Use the lowercase, relative form of the command. Defaults to False.

        Returns
        -------
        Path
            This path, for chaining.

        See Also
        --------
        quad_to : Give the control point explicitly.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(0, 0).quad_to(1, 2, 3, 4).smooth_quad_to(5, 6).d)
        'M0 0 Q1 2 3 4 T5 6'
        """
        return self._push(SmoothQuadTo(x, y, relative=relative))

    def arc_to(
        self, rx: float, ry: float, x: float, y: float, *, rotation: float = 0.0, large: bool = False,
        clockwise: bool = True, relative: bool = False,
    ) -> Self:
        """Draw an elliptical arc.

        `large` and `clockwise` correspond to SVG's ``large-arc-flag`` and
        ``sweep-flag``.

        Parameters
        ----------
        rx, ry : float
            Ellipse radii.
        x, y : float
            End point.
        rotation : float, optional
            Angle of the ellipse's x-axis in degrees. Defaults to 0.0.
        large : bool, optional
            Take the arc spanning more than 180 degrees. Defaults to False.
        clockwise : bool, optional
            Sweep in the positive-angle direction. Defaults to True.
        relative : bool, optional
            Use the lowercase, relative form of the command. Defaults to False.

        Returns
        -------
        Path
            This path, for chaining.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(0, 0).arc_to(5, 5, 10, 10, large=True).d)
        'M0 0 A5 5 0 1 1 10 10'
        """
        return self._push(ArcTo(rx, ry, rotation, large, clockwise, x, y, relative=relative))

    def close(self) -> Self:
        """Close the current subpath with a straight segment.

        Returns
        -------
        Path
            This path, for chaining.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path().move_to(0, 0).line_to(5, 0).close().d)
        'M0 0 L5 0 Z'
        """
        return self._push(ClosePath())

    @classmethod
    def build(cls, builder: PathBuilder, **kwargs: Any) -> Self:
        """Create a path from a finished builder.

        Parameters
        ----------
        builder : PathBuilder
            The builder whose data to use.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Path
            The new path.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path.build(svg.PathBuilder().move_to(0, 0).line_to(1, 1)))
        '<path d="M0 0 L1 1"/>'
        """
        return cls(builder.build(), **kwargs)
