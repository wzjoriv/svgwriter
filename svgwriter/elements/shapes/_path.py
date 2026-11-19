"""``<path>`` and its composition operators."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar, overload

import numpy as np

from ..._internal._typing import Self
from ...attributes.descriptors import Attr
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
from ...pathdata.data import BBox, PathData, PathDataLike
from .._geometry import Operand
from .._transformable import offset
from ..base import Element
from ._base import Shape

if TYPE_CHECKING:
    from ..structure import Group

__all__ = ["Path"]


class Path(Shape, tag="path"):
    """``<path>``: an arbitrary outline described by path data.

    Drawing methods append commands to ``d`` and return the path, so paths
    can be built fluently, and paths combine with the operators of
    :class:`~svgwriter.elements.PathOperand`.

    Parameters
    ----------
    d : str, PathData, PathBuilder or iterable of commands, optional
        The path data. Defaults to an empty path.
    path_length : float, optional
        Author's computed total length. Defaults to None.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Polyline : Straight segments from a point array.
    svgwriter.PathBuilder : Build path data without an element.

    Notes
    -----
    ``p1 + p2`` appends ``p2``'s subpaths to a copy of ``p1``; ``p += p2``
    does it in place, as do ``|=``, ``&=``, ``-=`` and ``^=`` for the
    boolean operations.

    Drawing methods append to ``d`` and return the path, so a path can be
    built fluently: ``path().move_to(0, 0).line_to(10, 0).close()``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Path().move_to(0, 0).line_to(10, 0).arc_to(5, 5, 10, 10).close().d)
    'M0 0 L10 0 A5 5 0 0 1 10 10 Z'
    >>> a = svg.Path("M0 0 H10", stroke="red")
    >>> str(a + svg.Path("M0 5 H10"))
    '<path d="M0 0 H10 M0 5 H10" stroke="red"/>'
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"d", "pathLength"})
    path_length = Attr[float](convert=float)

    def __init__(self, d: PathDataLike | PathBuilder = "", *, path_length: float | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.d = d  # type: ignore[assignment]
        self.update(path_length=path_length)

    @property
    def d(self) -> PathData:
        """The path data; assign a string, :class:`PathData` or builder.

        Examples
        --------
        >>> import svgwriter as svg
        >>> p = svg.Path("M0 0 L10 0")
        >>> p.d = "M5 5 H20"
        >>> str(p)
        '<path d="M5 5 H20"/>'
        """
        raw = self.attributes.get("d", "")
        return raw if isinstance(raw, PathData) else PathData(raw)

    @d.setter
    def d(self, value: PathDataLike | PathBuilder) -> None:
        if isinstance(value, PathBuilder):
            value = value.build()
        self.attributes["d"] = value if isinstance(value, PathData) else PathData(value)

    @property
    def nodes(self) -> np.ndarray:
        """All end and control points as an ``(N, 2)`` array; assign to move them.

        Assigning rewrites ``d`` in absolute form. Broadcasting works as in
        numpy: ``p.nodes = p.nodes * [1, -1] + 5``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> p = svg.Path("M0 0 L10 0 L10 10")
        >>> p.nodes = p.nodes + [1, 2]
        >>> str(p.d)
        'M1 2 L11 2 L11 12'
        """
        return self.d.nodes()

    @nodes.setter
    def nodes(self, value: object) -> None:
        self.d = self.d.with_nodes(value)

    def _push(self, command: PathCommand) -> Self:
        self.attributes["d"] = PathData((*self.d, command))
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
        >>> str(svg.Path().line_to(1, 2).d)
        'L1 2'
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
        >>> str(svg.Path().horizontal_to(5).d)
        'H5'
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
        >>> str(svg.Path().vertical_to(6, relative=True).d)
        'v6'
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
        >>> str(svg.Path().curve_to(1, 2, 3, 4, 5, 6).d)
        'C1 2 3 4 5 6'
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
        >>> str(svg.Path().curve_to(1, 2, 3, 4, 5, 6).smooth_curve_to(7, 8, 9, 10).d)
        'C1 2 3 4 5 6 S7 8 9 10'
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
        >>> str(svg.Path().quad_to(1, 2, 3, 4).d)
        'Q1 2 3 4'
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
        >>> str(svg.Path().quad_to(1, 2, 3, 4).smooth_quad_to(5, 6).d)
        'Q1 2 3 4 T5 6'
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
        >>> str(svg.Path().arc_to(5, 5, 10, 10, large=True).d)
        'A5 5 0 1 1 10 10'
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

    @classmethod
    def from_points(cls, points: Iterable[tuple[float, float]], *, closed: bool = False, **kwargs: Any) -> Self:
        """Create a path through a sequence of points.

        Parameters
        ----------
        points : iterable of tuple of float
            Vertices ``(x, y)``; the first starts the path.
        closed : bool, optional
            Close the path back to the first point. Defaults to False.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Path
            The new path.

        See Also
        --------
        Polyline : The same outline as a ``<polyline>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Path.from_points([(0, 0), (5, 0), (5, 5)], closed=True))
        '<path d="M0 0 L5 0 L5 5 Z"/>'
        """
        builder = PathBuilder()
        for i, (x, y) in enumerate(points):
            if i == 0:
                builder.move_to(x, y)
            else:
                builder.line_to(x, y)
        if closed:
            builder.close()
        return cls(builder, **kwargs)

    @property
    def bbox(self) -> BBox:
        """Geometric bounding box of the path data; empty paths give a zero box.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Path("M0 0 L10 5").bbox
        BBox(x=0.0, y=0.0, width=10.0, height=5.0)
        """
        return self.d.bbox or BBox(0.0, 0.0, 0.0, 0.0)

    def local_outline(self) -> PathData:
        """The path data itself."""
        return self.d

    def _replace(self, data: PathData) -> Self:
        self.d = data
        self.discard("transform")
        return self

    @overload
    def __add__(self, other: Path | PathData | str) -> Path: ...
    @overload
    def __add__(self, other: Element | Iterable[Element]) -> Group: ...
    def __add__(self, other: Path | PathData | str | Element | Iterable[Element]) -> Path | Group:
        if isinstance(other, (Path, PathData, str)):
            clone = self.clone()
            clone.d = self.d + (other.d if isinstance(other, Path) else other)
            return clone
        return super().__add__(other)

    def __iadd__(self, other: Path | PathData | str) -> Self:
        if not isinstance(other, (Path, PathData, str)):
            return super().__iadd__(other)  # type: ignore[no-any-return]
        self.d = self.d + (other.d if isinstance(other, Path) else other)
        return self

    def __ior__(self, other: Operand) -> Self:
        result = self.__or__(other)
        return NotImplemented if result is NotImplemented else self._replace(result.d)

    def __iand__(self, other: Operand) -> Self:
        result = self.__and__(other)
        return NotImplemented if result is NotImplemented else self._replace(result.d)

    def __isub__(self, other: Operand) -> Self:
        if offset(other) is not None:
            return super().__isub__(other)  # type: ignore[no-any-return]
        result = self.__sub__(other)
        return NotImplemented if result is NotImplemented else self._replace(result.d)

    def __ixor__(self, other: Operand) -> Self:
        result = self.__xor__(other)
        return NotImplemented if result is NotImplemented else self._replace(result.d)
