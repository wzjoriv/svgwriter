"""
``<path>`` and its composition operators.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar, overload

import numpy as np

from ..._internal._typing import Self
from ...attributes.descriptors import Attr
from ...pathdata.builder import PathBuilder
from ...pathdata.data import BBox, PathData, PathDataLike
from .._behavior import Operand, offset
from ..core import Element
from ._base import Shape
from ._commands import PathCommands

if TYPE_CHECKING:
    from ...inkscape.connectors import Connection
    from ..structure import Group

__all__ = ["Path"]


class Path(PathCommands, Shape, tag="path"):
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
    def connects(self) -> Connection | None:
        """The objects this path joins as an Inkscape connector, or None for a plain path.

        Assign ``(start, end)`` to attach the path to two elements
        (``inkscape:connection-start`` and ``-end``; it is redrawn as a straight
        line between their centres), or None to detach it.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 40)
        >>> a, b = doc.circle(10, 20, 5), doc.circle(90, 20, 5)
        >>> wire = doc.path(stroke="black")
        >>> wire.connects = (a, b)
        >>> wire.connects.start is a, str(wire.d)
        (True, 'M10 20 L90 20')
        """
        from ...inkscape.connectors import connection

        return connection(self)

    @connects.setter
    def connects(self, value: tuple[Element | None, Element | None] | None) -> None:
        from ...inkscape.connectors import connect

        start, end = (None, None) if value is None else value
        connect(self, start, end)

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
