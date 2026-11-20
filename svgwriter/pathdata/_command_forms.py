"""
Letter, absolute form and text shared by every path command.
"""

from __future__ import annotations

from dataclasses import fields, replace
from typing import Any, ClassVar

from .._internal._constants import DEFAULT_PRECISION
from .._internal._numbers import format_number
from .._internal._typing import Self
from ..transform.matrix import Point

__all__ = ["CommandForms", "XYEnd"]


class CommandForms:
    """Written forms of :class:`~svgwriter.pathdata.PathCommand`: letter, absolute equivalent and text."""

    code: ClassVar[str]
    coordinates: ClassVar[tuple[str, ...]]
    relative: bool
    arguments: Any

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


def _values(command: Any) -> tuple[float, ...]:
    return tuple(
        float(getattr(command, f.name)) for f in fields(command)  # type: ignore[arg-type]
        if f.name != "relative"
    )


class XYEnd:
    """Shared behaviour for commands that end at ``(x, y)``."""

    x: float
    y: float
    relative: bool

    def end_point(self, current: Point, start: Point) -> Point:
        x, y = self.x, self.y
        return Point(current.x + x, current.y + y) if self.relative else Point(x, y)

    @property
    def arguments(self) -> tuple[float, ...]:
        return _values(self)
