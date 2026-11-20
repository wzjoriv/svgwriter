"""
Immutable path data with normalization and bounding boxes.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from functools import cached_property
from typing import Any, NamedTuple, overload

from .._internal._constants import DEFAULT_PRECISION
from .._internal._drawable import Drawable, box_picture, path_picture
from .._internal._numbers import format_number
from ..transform.matrix import Matrix, Point
from ..transform.transform import TransformLike
from ._constants import BOX_POINTS, IMPLIED
from ._geometry import PathGeometry
from .commands import (
    PathCommand,
)
from .parser import parse_path

__all__ = ["BBox", "PathData", "PathDataLike"]



def _short_number(text: str) -> str:
    if text.startswith("0."):
        return text[1:]
    if text.startswith("-0."):
        return "-" + text[2:]
    return text


class BBox(NamedTuple):
    """Axis-aligned bounding box.

    A named tuple, so it unpacks as ``x, y, width, height``.

    Parameters
    ----------
    x, y : float
        Top-left corner.
    width, height : float
        Extent along each axis.

    See Also
    --------
    PathData.bbox : The bounding box of path data.

    Examples
    --------
    >>> from svgwriter.pathdata import BBox
    >>> x, y, w, h = BBox(1, 2, 3, 4)
    >>> w, h
    (3, 4)
    """

    x: float
    y: float
    width: float
    height: float

    @classmethod
    def from_points(cls, points: Iterable[Point | tuple[float, float]]) -> BBox:
        """Return the smallest box containing every point.

        Parameters
        ----------
        points : iterable of Point or tuple of float
            The points to enclose.

        Returns
        -------
        BBox
            The enclosing box; an empty input gives a zero box at the origin.

        Examples
        --------
        >>> from svgwriter.pathdata import BBox
        >>> BBox.from_points([(0, 0), (4, 2)])
        BBox(x=0, y=0, width=4, height=2)
        """
        pairs = list(points)
        if not pairs:
            return cls(0.0, 0.0, 0.0, 0.0)
        xs, ys = zip(*pairs, strict=True)
        return cls(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    @property
    def center(self) -> Point:
        """The centre of the box.

        Examples
        --------
        >>> from svgwriter.pathdata import BBox
        >>> BBox(0, 0, 4, 2).center
        Point(x=2.0, y=1.0)
        """
        return Point(self.x + self.width / 2.0, self.y + self.height / 2.0)

    @property
    def left(self) -> float:
        """Smallest x."""
        return self.x

    @property
    def right(self) -> float:
        """Largest x."""
        return self.x + self.width

    @property
    def top(self) -> float:
        """Smallest y (SVG's y axis points down)."""
        return self.y

    @property
    def bottom(self) -> float:
        """Largest y."""
        return self.y + self.height

    top_left = property(lambda self: self.point("top_left"), doc="Corner at ``(left, top)``.")
    top_center = property(lambda self: self.point("top_center"), doc="Middle of the top edge.")
    top_right = property(lambda self: self.point("top_right"), doc="Corner at ``(right, top)``.")
    center_left = property(lambda self: self.point("center_left"), doc="Middle of the left edge.")
    center_right = property(lambda self: self.point("center_right"), doc="Middle of the right edge.")
    bottom_left = property(lambda self: self.point("bottom_left"), doc="Corner at ``(left, bottom)``.")
    bottom_center = property(lambda self: self.point("bottom_center"), doc="Middle of the bottom edge.")
    bottom_right = property(lambda self: self.point("bottom_right"), doc="Corner at ``(right, bottom)``.")

    def point(self, name: str) -> Point:
        """A named point of the box.

        Parameters
        ----------
        name : str
            ``"center"``, a corner (``"top_left"``, ``"top_right"``,
            ``"bottom_left"``, ``"bottom_right"``), an edge middle
            (``"top_center"``, ``"center_left"``, ...), or an edge name
            (``"top"``, ``"left"``, ...) meaning that edge's middle.

        Returns
        -------
        Point
            The point in the box's coordinates.

        Raises
        ------
        ValueError
            If the name is unknown.

        Examples
        --------
        >>> from svgwriter.pathdata import BBox
        >>> box = BBox(0, 0, 4, 2)
        >>> box.point("top_right"), box.point("bottom"), box.bottom_left
        (Point(x=4.0, y=0.0), Point(x=2.0, y=2.0), Point(x=0.0, y=2.0))
        """
        try:
            fx, fy = BOX_POINTS[name]
        except KeyError:
            raise ValueError(f"unknown box point {name!r}; choose one of {', '.join(BOX_POINTS)}") from None
        return Point(self.x + fx * self.width, self.y + fy * self.height)

    def __svgwriter__(self) -> Any:
        """The box as a dashed rectangle (``doc.add(box)``, notebook display)."""
        return box_picture(self)

    def _repr_svg_(self) -> str | None:
        return box_picture(self)._repr_svg_()  # type: ignore[no-any-return]

    def union(self, other: BBox) -> BBox:
        """Return the smallest box containing this box and another.

        Parameters
        ----------
        other : BBox
            The box to merge with.

        Returns
        -------
        BBox
            The combined box.

        Examples
        --------
        >>> from svgwriter.pathdata import BBox
        >>> BBox(0, 0, 4, 2).union(BBox(10, 10, 1, 1))
        BBox(x=0, y=0, width=11, height=11)
        """
        return BBox.from_points(
            [(self.x, self.y), (self.x + self.width, self.y + self.height),
             (other.x, other.y), (other.x + other.width, other.y + other.height)]
        )


class PathData(PathGeometry, Drawable, Sequence[PathCommand]):
    """A parsed, immutable sequence of path commands.

    Supports indexing, slicing, iteration, concatenation with ``+`` and
    transformation with ``@``. Instances are hashable and compare by their commands.

    Parameters
    ----------
    commands : str or iterable of PathCommand, optional
        Path data text, or commands. Defaults to an empty path.

    Raises
    ------
    PathSyntaxError
        If `commands` is text that is not valid path data.

    See Also
    --------
    PathBuilder : Fluent construction of path data.

    Examples
    --------
    >>> from svgwriter.pathdata import PathData
    >>> from svgwriter.transform import Matrix
    >>> d = PathData("M0 0 h10 v10 z")
    >>> str(d.to_absolute())
    'M0 0 H10 V10 Z'
    >>> d.bbox
    BBox(x=0.0, y=0.0, width=10.0, height=10.0)
    >>> str(Matrix.translate(5, 0) @ d)
    'M5 0 L15 0 L15 10 Z'
    >>> len((d + "M20 20 h5").subpaths())
    2
    """

    def __init__(self, commands: str | Iterable[PathCommand] = ()) -> None:
        if isinstance(commands, str):
            self._commands: tuple[PathCommand, ...] = tuple(parse_path(commands))
        else:
            self._commands = tuple(commands)

    @overload
    def __getitem__(self, index: int) -> PathCommand: ...
    @overload
    def __getitem__(self, index: slice) -> PathData: ...
    def __getitem__(self, index: int | slice) -> PathCommand | PathData:
        if isinstance(index, slice):
            return PathData(self._commands[index])
        return self._commands[index]

    def __len__(self) -> int:
        return len(self._commands)

    def __iter__(self) -> Iterator[PathCommand]:
        return iter(self._commands)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PathData) and self._commands == other._commands

    def __hash__(self) -> int:
        return hash(self._commands)

    def __add__(self, other: PathData | str) -> PathData:
        if isinstance(other, str):
            other = PathData(other)
        if not isinstance(other, PathData):
            return NotImplemented
        return PathData(self._commands + other._commands)

    def __radd__(self, other: PathData | str | int) -> PathData:
        if isinstance(other, int) and other == 0:
            return self
        if isinstance(other, str):
            return PathData(other) + self
        return NotImplemented

    def __matmul__(self, transform: TransformLike) -> PathData:
        """Return the data with coordinates mapped through a transform (``data @ M``)."""
        if not isinstance(transform, (str, Matrix)) and not hasattr(transform, "to_matrix"):
            return NotImplemented
        return self.transformed(transform)

    def __rmatmul__(self, transform: TransformLike) -> PathData:
        return self.__matmul__(transform)

    def __repr__(self) -> str:
        return f"PathData({str(self)!r})"

    @cached_property
    def bbox(self) -> BBox | None:
        """Approximate bounding box, or ``None`` for empty data.

        Computed from sampled outline points, so curves are approximate.

        Returns
        -------
        BBox or None
            The box around the sampled points, or ``None`` when there are none.

        Examples
        --------
        >>> from svgwriter.pathdata import PathData
        >>> PathData("M0 0 L10 0 L10 10").bbox
        BBox(x=0.0, y=0.0, width=10.0, height=10.0)
        >>> PathData().bbox is None
        True
        """
        points = list(self.points())
        return BBox.from_points(points) if points else None

    def __svgwriter__(self) -> Any:
        """The outline as a thin unfilled ``<path>`` (``doc.add(data)``, notebook display)."""
        return path_picture(self)

    def svg_value(self, precision: int = DEFAULT_PRECISION, *, compact: bool = False) -> str:
        """Serialize the path as text for the ``d`` attribute.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places. Defaults to the library default precision.
        compact : bool, optional
            Drop repeated command letters and unneeded spaces. Defaults to False.

        Returns
        -------
        str
            The path data text.

        Examples
        --------
        >>> from svgwriter.pathdata import PathData
        >>> d = PathData("M0 0.5 L1.25 -0.5 L3 3")
        >>> d.svg_value()
        'M0 0.5 L1.25 -0.5 L3 3'
        >>> d.svg_value(compact=True)
        'M0 .5 1.25-.5 3 3'
        """
        if not compact:
            return " ".join(command.svg_value(precision) for command in self._commands)
        out: list[str] = []
        previous = ""
        for command in self._commands:
            letter = command.letter
            needs_separator = letter == IMPLIED.get(previous, previous) and letter not in "Zz"
            if not needs_separator:
                out.append(letter)
            for value in command.arguments:
                text = _short_number(format_number(value, precision))
                if needs_separator and not text.startswith("-"):
                    out.append(" ")
                out.append(text)
                needs_separator = True
            previous = letter
        return "".join(out)

    def __str__(self) -> str:
        return self.svg_value()


PathDataLike = PathData | str | Iterable[PathCommand]
