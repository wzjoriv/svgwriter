"""
``polyline`` and ``polygon``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, ClassVar, Final

import numpy as np

from ..._internal._constants import DEFAULT_PRECISION
from ..._internal._numbers import format_number
from ..._internal._typing import Self
from ...pathdata.builder import PathBuilder
from ...pathdata.data import BBox, PathData
from ._base import Shape, parse_points

PointsLike = np.ndarray | Sequence[Sequence[float]]
_EMPTY: Final = np.zeros((0, 2))
_EMPTY.flags.writeable = False


class PointList:
    """Immutable ``points`` attribute value wrapping an ``(N, 2)`` array.

    Parameters
    ----------
    array : numpy.ndarray
        Read-only ``(N, 2)`` float array of vertices.

    See Also
    --------
    as_points : Build such an array from other inputs.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter.elements.shapes._poly import PointList
    >>> PointList(np.array([[0.0, 0.0], [1.0, 2.0]]))
    PointList([[0.0, 0.0], [1.0, 2.0]])
    """

    __slots__ = ("array",)

    def __init__(self, array: np.ndarray) -> None:
        self.array = array

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PointList) and np.array_equal(self.array, other.array)

    def __hash__(self) -> int:
        return hash(self.array.tobytes())

    def __array__(self, dtype: Any = None, copy: Any = None) -> np.ndarray:
        return self.array if dtype is None else self.array.astype(dtype)

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize as SVG ``points`` text.

        Parameters
        ----------
        precision : int, optional
            Maximum decimal places. Defaults to the library default.

        Returns
        -------
        str
            Space-separated ``x,y`` pairs.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.shapes._poly import PointList
        >>> PointList(np.array([[0.0, 0.0], [1.5, 2.0]])).svg_value()
        '0,0 1.5,2'
        """
        return " ".join(f"{format_number(x, precision)},{format_number(y, precision)}" for x, y in self.array.tolist())

    def __repr__(self) -> str:
        return f"PointList({self.array.tolist()!r})"


def as_points(value: PointsLike | str) -> np.ndarray:
    """Convert point input to a read-only ``(N, 2)`` float array.

    Parameters
    ----------
    value : array-like or str
        Vertices as a sequence of pairs, an array or SVG points text.

    Returns
    -------
    numpy.ndarray
        Read-only float array of shape ``(N, 2)``; empty input gives ``(0, 2)``.

    Raises
    ------
    ValueError
        If the input does not have shape ``(N, 2)``.

    Examples
    --------
    >>> from svgwriter.elements.shapes._poly import as_points
    >>> as_points("0,0 1,2").tolist()
    [[0.0, 0.0], [1.0, 2.0]]
    """
    array = np.array(parse_points(value) if isinstance(value, str) else value, dtype=float)
    if array.size == 0:
        return _EMPTY
    if array.ndim != 2 or array.shape[1] != 2:
        raise ValueError(f"points must have shape (N, 2), got {array.shape}")
    array.flags.writeable = False
    return array

__all__ = ["PointList", "PointsLike", "Polygon", "Polyline", "as_points"]

DEFAULT_SIDES: Final = 6

FULL_CIRCLE: Final = 360.0


class Polyline(Shape, tag="polyline"):
    """``<polyline>``: an open sequence of straight segments.

    Parameters
    ----------
    points : array-like or str, optional
        Vertices as ``(N, 2)`` pairs or SVG points text. Defaults to no points.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Polygon : The closed variant.
    Path.from_points : The same outline as a ``<path>``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Polyline([(0, 0), (1, 2)]))
    '<polyline points="0,0 1,2"/>'
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"points"})

    def __init__(self, points: PointsLike | str = (), **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.points = points  # type: ignore[assignment]

    @property
    def points(self) -> np.ndarray:
        """Vertices as a read-only ``(N, 2)`` float array.

        Assign any ``(N, 2)`` array-like or SVG points text to replace them.

        Examples
        --------
        >>> import svgwriter as svg
        >>> line = svg.Polyline("0,0 1,2")
        >>> line.points.tolist()
        [[0.0, 0.0], [1.0, 2.0]]
        >>> line.points = [(5, 5), (6, 6)]
        >>> str(line)
        '<polyline points="5,5 6,6"/>'
        """
        raw = self.attributes.get("points")
        if raw is None:
            return _EMPTY
        if not isinstance(raw, PointList):
            raw = PointList(as_points(raw))
            self.attributes["points"] = raw
        return raw.array

    @points.setter
    def points(self, value: PointsLike | str) -> None:
        self.attributes["points"] = PointList(as_points(value))

    @classmethod
    def regular(cls, cx: float, cy: float, radius: float, sides: int = DEFAULT_SIDES, **kwargs: Any) -> Self:
        """Create the vertices of a regular polygon.

        The first vertex is at the top and the rest follow clockwise.

        Parameters
        ----------
        cx, cy : float
            Center.
        radius : float
            Distance from the center to each vertex.
        sides : int, optional
            Number of vertices. Defaults to 6.
        **kwargs
            Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Polyline
            The new element; on :class:`Polygon` it is closed.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Polygon.regular(0, 0, 10, 4))
        '<polygon points="0,-10 10,0 0,10 -10,0"/>'
        """
        step = FULL_CIRCLE / sides
        angles = np.radians(np.arange(sides) * step)
        return cls(np.column_stack((cx + radius * np.sin(angles), cy - radius * np.cos(angles))), **kwargs)

    @property
    def bbox(self) -> BBox:
        """Geometric bounding box of the vertices; no points give a zero box.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Polyline([(0, 0), (4, 3)]).bbox
        BBox(x=0.0, y=0.0, width=4.0, height=3.0)
        """
        pts = self.points
        if not len(pts):
            return BBox(0.0, 0.0, 0.0, 0.0)
        low, high = pts.min(axis=0), pts.max(axis=0)
        return BBox(float(low[0]), float(low[1]), float(high[0] - low[0]), float(high[1] - low[1]))

    def _builder(self) -> PathBuilder:
        builder = PathBuilder()
        for index, (x, y) in enumerate(self.points.tolist()):
            if index == 0:
                builder.move_to(x, y)
            else:
                builder.line_to(x, y)
        return builder

    def local_outline(self) -> PathData:
        return self._builder().build()


class Polygon(Polyline, tag="polygon"):
    """``<polygon>``: a closed ``Polyline``.

    Takes the same parameters as :class:`Polyline`; the last vertex joins the first.

    Parameters
    ----------
    points : array-like or str, optional
        Vertices as ``(N, 2)`` pairs or SVG points text. Defaults to no points.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Polyline : The open variant.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Polygon([(0, 0), (4, 0), (4, 3)]))
    '<polygon points="0,0 4,0 4,3"/>'
    """

    @property
    def area(self) -> float:
        """Enclosed area from the shoelace formula, in square user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Polygon([(0, 0), (4, 0), (4, 3)]).area
        6.0
        """
        x, y = self.points.T
        return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2.0)

    def local_outline(self) -> PathData:
        builder = self._builder()
        return builder.close().build() if len(builder) else builder.build()
