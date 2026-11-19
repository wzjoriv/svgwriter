"""Path segment commands (M, L, H, V, C, S, Q, T, A, Z)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields, replace
from typing import ClassVar

from .._internal._constants import DEFAULT_PRECISION
from .._internal._numbers import format_number
from .._internal._typing import Self
from ..transform.matrix import Point

__all__ = [
    "ArcTo",
    "ClosePath",
    "CurveTo",
    "HLineTo",
    "LineTo",
    "MoveTo",
    "PathCommand",
    "QuadTo",
    "SmoothCurveTo",
    "SmoothQuadTo",
    "VLineTo",
]


class PathCommand(ABC):
    """One segment of path data.

    Base class of the ten SVG path commands. Each command knows its letter, its
    numeric arguments and where it leaves the pen, and can be converted from
    relative to absolute form.

    Attributes
    ----------
    code : str
        The uppercase command letter.
    coordinates : tuple of str
        Names of the fields that are coordinates (shifted by the current point
        when relative).
    relative : bool
        Whether the command is in its lowercase (relative) form.

    See Also
    --------
    PathData : A sequence of commands.

    Examples
    --------
    >>> from svgwriter.pathdata import LineTo
    >>> isinstance(LineTo(1, 2), PathCommand)
    True
    """

    code: ClassVar[str]
    coordinates: ClassVar[tuple[str, ...]] = ()
    relative: bool

    @property
    def letter(self) -> str:
        """The command letter as written: uppercase, or lowercase when relative.

        Examples
        --------
        >>> from svgwriter.pathdata import MoveTo
        >>> MoveTo(1, 2, relative=True).letter
        'm'
        """
        return self.code.lower() if self.relative else self.code

    @property
    @abstractmethod
    def arguments(self) -> tuple[float, ...]:
        """Numbers written after the command letter, in order.

        Examples
        --------
        >>> from svgwriter.pathdata import LineTo
        >>> LineTo(1, 2).arguments
        (1.0, 2.0)
        """

    @abstractmethod
    def end_point(self, current: Point, start: Point) -> Point:
        """Return the absolute pen position after this segment.

        Parameters
        ----------
        current : Point
            Pen position before the command.
        start : Point
            Start of the current subpath, where ``Z`` returns to.

        Returns
        -------
        Point
            The pen position once the command has been drawn.

        Examples
        --------
        >>> from svgwriter.pathdata import LineTo
        >>> from svgwriter.transform import Point
        >>> LineTo(1, 2, relative=True).end_point(Point(10, 10), Point(0, 0))
        Point(x=11, y=12)
        """

    def to_absolute(self, current: Point) -> Self:
        """Return an absolute equivalent of the command.

        Parameters
        ----------
        current : Point
            Pen position before the command; relative coordinates are offsets from it.

        Returns
        -------
        PathCommand
            The command itself if already absolute, otherwise a new one.

        Examples
        --------
        >>> from svgwriter.pathdata import LineTo
        >>> from svgwriter.transform import Point
        >>> LineTo(1, 2, relative=True).to_absolute(Point(10, 10))
        LineTo(x=11, y=12, relative=False)
        """
        if not self.relative:
            return self
        offsets = {
            name: getattr(self, name) + (current.x if name.startswith("x") else current.y)
            for name in self.coordinates
        }
        return replace(self, relative=False, **offsets)  # type: ignore[type-var]

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize the command as path data text.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places. Defaults to the library default precision.

        Returns
        -------
        str
            The command letter followed by its arguments.

        Examples
        --------
        >>> from svgwriter.pathdata import LineTo
        >>> LineTo(1.23456, 2).svg_value(2)
        'L1.23 2'
        """
        args = " ".join(format_number(a, precision) for a in self.arguments)
        return f"{self.letter}{args}" if args else self.letter

    def __str__(self) -> str:
        return self.svg_value()


def _values(command: PathCommand) -> tuple[float, ...]:
    return tuple(
        float(getattr(command, f.name)) for f in fields(command)  # type: ignore[arg-type]
        if f.name != "relative"
    )


@dataclass(frozen=True)
class _XYCommand(PathCommand):
    """Shared behaviour for commands that end at ``(x, y)``."""

    def end_point(self, current: Point, start: Point) -> Point:
        x, y = self.x, self.y
        return Point(current.x + x, current.y + y) if self.relative else Point(x, y)

    @property
    def arguments(self) -> tuple[float, ...]:
        return _values(self)


@dataclass(frozen=True)
class MoveTo(_XYCommand):
    """Move the pen without drawing (``M``/``m``).

    Starts a new subpath at the given point.

    Parameters
    ----------
    x, y : float
        Target coordinates (offsets when relative).
    relative : bool, optional
        Use the lowercase (relative) form; keyword-only. Defaults to False.

    See Also
    --------
    LineTo : Draw to a point.

    Examples
    --------
    >>> from svgwriter.pathdata import MoveTo
    >>> str(MoveTo(1, 2))
    'M1 2'
    """
    code: ClassVar[str] = "M"
    coordinates: ClassVar[tuple[str, ...]] = ("x", "y")
    x: float
    y: float
    relative: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class LineTo(_XYCommand):
    """Draw a straight line (``L``/``l``).

    Draws from the current point to the given point.

    Parameters
    ----------
    x, y : float
        End point (offsets when relative).
    relative : bool, optional
        Use the lowercase (relative) form; keyword-only. Defaults to False.

    See Also
    --------
    MoveTo : Move without drawing.

    Examples
    --------
    >>> from svgwriter.pathdata import LineTo
    >>> str(LineTo(1, 2, relative=True))
    'l1 2'
    """
    code: ClassVar[str] = "L"
    coordinates: ClassVar[tuple[str, ...]] = ("x", "y")
    x: float
    y: float
    relative: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class HLineTo(PathCommand):
    """Draw a horizontal line (``H``/``h``).

    Draws to a new x coordinate, keeping y.

    Parameters
    ----------
    x : float
        Target x coordinate (an offset when relative).
    relative : bool, optional
        Use the lowercase (relative) form; keyword-only. Defaults to False.

    See Also
    --------
    VLineTo : The vertical counterpart.

    Examples
    --------
    >>> from svgwriter.pathdata import HLineTo
    >>> str(HLineTo(5))
    'H5'
    """
    code: ClassVar[str] = "H"
    coordinates: ClassVar[tuple[str, ...]] = ("x",)
    x: float
    relative: bool = field(default=False, kw_only=True)

    @property
    def arguments(self) -> tuple[float, ...]:
        return (self.x,)

    def end_point(self, current: Point, start: Point) -> Point:
        return Point(current.x + self.x if self.relative else self.x, current.y)


@dataclass(frozen=True)
class VLineTo(PathCommand):
    """Draw a vertical line (``V``/``v``).

    Draws to a new y coordinate, keeping x.

    Parameters
    ----------
    y : float
        Target y coordinate (an offset when relative).
    relative : bool, optional
        Use the lowercase (relative) form; keyword-only. Defaults to False.

    See Also
    --------
    HLineTo : The horizontal counterpart.

    Examples
    --------
    >>> from svgwriter.pathdata import VLineTo
    >>> str(VLineTo(5, relative=True))
    'v5'
    """
    code: ClassVar[str] = "V"
    coordinates: ClassVar[tuple[str, ...]] = ("y",)
    y: float
    relative: bool = field(default=False, kw_only=True)

    @property
    def arguments(self) -> tuple[float, ...]:
        return (self.y,)

    def end_point(self, current: Point, start: Point) -> Point:
        return Point(current.x, current.y + self.y if self.relative else self.y)


@dataclass(frozen=True)
class CurveTo(_XYCommand):
    """Cubic Bezier with two explicit control points (``C``/``c``).

    Parameters
    ----------
    x1, y1 : float
        First control point.
    x2, y2 : float
        Second control point.
    x, y : float
        End point.
    relative : bool, optional
        Use the lowercase (relative) form; keyword-only. Defaults to False.

    See Also
    --------
    SmoothCurveTo : Cubic curve with a reflected first control point.

    Examples
    --------
    >>> from svgwriter.pathdata import CurveTo
    >>> str(CurveTo(1, 2, 3, 4, 5, 6))
    'C1 2 3 4 5 6'
    """

    code: ClassVar[str] = "C"
    coordinates: ClassVar[tuple[str, ...]] = ("x1", "y1", "x2", "y2", "x", "y")
    x1: float
    y1: float
    x2: float
    y2: float
    x: float
    y: float
    relative: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class SmoothCurveTo(_XYCommand):
    """Cubic Bezier whose first control point is reflected (``S``/``s``).

    Parameters
    ----------
    x2, y2 : float
        Second control point.
    x, y : float
        End point.
    relative : bool, optional
        Use the lowercase (relative) form; keyword-only. Defaults to False.

    See Also
    --------
    CurveTo : Cubic curve with two explicit control points.

    Examples
    --------
    >>> from svgwriter.pathdata import SmoothCurveTo
    >>> str(SmoothCurveTo(3, 4, 5, 6))
    'S3 4 5 6'
    """

    code: ClassVar[str] = "S"
    coordinates: ClassVar[tuple[str, ...]] = ("x2", "y2", "x", "y")
    x2: float
    y2: float
    x: float
    y: float
    relative: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class QuadTo(_XYCommand):
    """Quadratic Bezier curve (``Q``/``q``).

    A curve with a single explicit control point.

    Parameters
    ----------
    x1, y1 : float
        Control point.
    x, y : float
        End point.
    relative : bool, optional
        Use the lowercase (relative) form; keyword-only. Defaults to False.

    See Also
    --------
    SmoothQuadTo : Quadratic curve with a reflected control point.

    Examples
    --------
    >>> from svgwriter.pathdata import QuadTo
    >>> str(QuadTo(1, 2, 3, 4))
    'Q1 2 3 4'
    """
    code: ClassVar[str] = "Q"
    coordinates: ClassVar[tuple[str, ...]] = ("x1", "y1", "x", "y")
    x1: float
    y1: float
    x: float
    y: float
    relative: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class SmoothQuadTo(_XYCommand):
    """Quadratic Bezier with a reflected control point (``T``/``t``).

    The control point is the reflection of the previous quadratic curve's control point.

    Parameters
    ----------
    x, y : float
        End point.
    relative : bool, optional
        Use the lowercase (relative) form; keyword-only. Defaults to False.

    See Also
    --------
    QuadTo : Quadratic curve with an explicit control point.

    Examples
    --------
    >>> from svgwriter.pathdata import SmoothQuadTo
    >>> str(SmoothQuadTo(3, 4))
    'T3 4'
    """
    code: ClassVar[str] = "T"
    coordinates: ClassVar[tuple[str, ...]] = ("x", "y")
    x: float
    y: float
    relative: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class ArcTo(_XYCommand):
    """Elliptical arc (``A``/``a``).

    The two flags select one of the four candidate arcs through the endpoints.

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
        End point (offsets when relative).
    relative : bool, optional
        Use the lowercase (relative) form; keyword-only. Defaults to False.

    See Also
    --------
    svgwriter.pathdata.endpoint_to_center : Convert to center parameterization.

    Examples
    --------
    >>> from svgwriter.pathdata import ArcTo
    >>> str(ArcTo(5, 5, 0, False, True, 10, 0))
    'A5 5 0 0 1 10 0'
    """

    code: ClassVar[str] = "A"
    coordinates: ClassVar[tuple[str, ...]] = ("x", "y")
    rx: float
    ry: float
    rotation: float
    large_arc: bool
    sweep: bool
    x: float
    y: float
    relative: bool = field(default=False, kw_only=True)

    @property
    def arguments(self) -> tuple[float, ...]:
        return (self.rx, self.ry, self.rotation, int(self.large_arc), int(self.sweep), self.x, self.y)


@dataclass(frozen=True)
class ClosePath(PathCommand):
    """Close the current subpath (``Z``/``z``).

    Draws a straight line back to the subpath's start and returns the pen there.

    Parameters
    ----------
    relative : bool, optional
        Use the lowercase form; keyword-only and equivalent to the uppercase one. Defaults to False.

    Examples
    --------
    >>> from svgwriter.pathdata import ClosePath
    >>> str(ClosePath())
    'Z'
    """

    code: ClassVar[str] = "Z"
    relative: bool = field(default=False, kw_only=True)

    @property
    def arguments(self) -> tuple[float, ...]:
        return ()

    def end_point(self, current: Point, start: Point) -> Point:
        return start
