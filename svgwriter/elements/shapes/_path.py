"""``<path>`` and its composition operators."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar, overload

import numpy as np

from ..._internal._typing import Self
from ...attributes.descriptors import Attr
from ...path.builder import PathBuilder
from ...path.commands import (
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
from ...path.data import BBox, PathData, PathDataLike
from .._geometry import Operand
from .._transformable import offset
from ..base import Element
from ._base import Shape

if TYPE_CHECKING:
    from ..structure import Group

__all__ = ["Path"]


class Path(Shape, tag="path"):
    """``<path>``.

    Parameters
    ----------
    d : str, PathData, PathBuilder or iterable of commands
        The path data.
    path_length : float, optional
        Author's computed total length.
    **kwargs
        Presentation, core, conditional and other attributes.

    Notes
    -----
    ``p1 + p2`` appends ``p2``'s subpaths to a copy of ``p1``; ``p += p2``
    does it in place, as do ``|=``, ``&=``, ``-=`` and ``^=`` for the
    boolean operations.

    Drawing methods append to ``d`` and return the path, so a path can be
    built fluently: ``path().move_to(0, 0).line_to(10, 0).close()``.

    Examples
    --------
    >>> str(Path().move_to(0, 0).line_to(10, 0).arc_to(5, 5, 10, 10).close().d)
    'M0 0 L10 0 A5 5 0 0 1 10 10 Z'
    >>> a = Path("M0 0 H10", stroke="red")
    >>> str(a + Path("M0 5 H10"))
    '<path stroke="red" d="M0 0 H10 M0 5 H10"/>'
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"d", "pathLength"})
    path_length = Attr[float](convert=float)

    def __init__(self, d: PathDataLike | PathBuilder = "", *, path_length: float | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.d = d  # type: ignore[assignment]
        self.update(path_length=path_length)

    @property
    def d(self) -> PathData:
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
        >>> p = Path("M0 0 L10 0 L10 10")
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
        """Start a new subpath at ``(x, y)``."""
        return self._push(MoveTo(x, y, relative=relative))

    def line_to(self, x: float, y: float, *, relative: bool = False) -> Self:
        """Straight line to ``(x, y)``."""
        return self._push(LineTo(x, y, relative=relative))

    def horizontal_to(self, x: float, *, relative: bool = False) -> Self:
        """Horizontal line to *x*."""
        return self._push(HLineTo(x, relative=relative))

    def vertical_to(self, y: float, *, relative: bool = False) -> Self:
        """Vertical line to *y*."""
        return self._push(VLineTo(y, relative=relative))

    def curve_to(
        self, x1: float, y1: float, x2: float, y2: float, x: float, y: float, *, relative: bool = False
    ) -> Self:
        """Cubic Bézier through control points ``(x1, y1)``, ``(x2, y2)`` to ``(x, y)``."""
        return self._push(CurveTo(x1, y1, x2, y2, x, y, relative=relative))

    def smooth_curve_to(self, x2: float, y2: float, x: float, y: float, *, relative: bool = False) -> Self:
        """Cubic Bézier whose first control point mirrors the previous one."""
        return self._push(SmoothCurveTo(x2, y2, x, y, relative=relative))

    def quad_to(self, x1: float, y1: float, x: float, y: float, *, relative: bool = False) -> Self:
        """Quadratic Bézier through ``(x1, y1)`` to ``(x, y)``."""
        return self._push(QuadTo(x1, y1, x, y, relative=relative))

    def smooth_quad_to(self, x: float, y: float, *, relative: bool = False) -> Self:
        """Quadratic Bézier whose control point mirrors the previous one."""
        return self._push(SmoothQuadTo(x, y, relative=relative))

    def arc_to(
        self, rx: float, ry: float, x: float, y: float, *, rotation: float = 0.0, large: bool = False,
        clockwise: bool = True, relative: bool = False,
    ) -> Self:
        """Elliptical arc with radii ``(rx, ry)`` to ``(x, y)``.

        *rotation* is the ellipse's x-axis angle in degrees; *large* picks
        the arc over 180 degrees and *clockwise* the sweep direction (SVG's
        ``large-arc-flag`` and ``sweep-flag``).
        """
        return self._push(ArcTo(rx, ry, rotation, large, clockwise, x, y, relative=relative))

    def close(self) -> Self:
        """Close the current subpath."""
        return self._push(ClosePath())

    @classmethod
    def build(cls, builder: PathBuilder, **kwargs: Any) -> Self:
        return cls(builder.build(), **kwargs)

    @classmethod
    def from_points(cls, points: Iterable[tuple[float, float]], *, closed: bool = False, **kwargs: Any) -> Self:
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
        return self.d.bbox or BBox(0.0, 0.0, 0.0, 0.0)

    def local_outline(self) -> PathData:
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
