"""
Lengths with units (``10``, ``2.5mm``, ``50%``).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Final, TypeAlias, overload

from .._internal._constants import (
    CM_PER_INCH,
    DEFAULT_DPI,
    DEFAULT_FONT_SIZE,
    DEFAULT_PRECISION,
    EX_PER_EM,
    MM_PER_INCH,
    PC_PER_INCH,
    PT_PER_INCH,
)
from .._internal._numbers import format_number
from ._constants import LENGTH_RE

__all__ = [
    "Length",
    "LengthLike",
    "LengthUnit",
    "Unit",
    "cm",
    "em",
    "ex",
    "inch",
    "mm",
    "pc",
    "percent",
    "pt",
    "px",
]


class Unit(str, enum.Enum):
    """SVG 1.1 length units.

    ``NONE`` (also ``USER``) means user units. ``PIXEL`` and ``INCH`` are
    aliases of ``PX`` and ``IN``. ``str(unit)`` gives the suffix as written in SVG.

    See Also
    --------
    Length : A value with a unit.

    Examples
    --------
    >>> from svgwriter.attributes import Unit
    >>> Unit("mm") is Unit.MM
    True
    >>> str(Unit.PERCENT)
    '%'
    """

    NONE = ""
    PX = "px"
    PT = "pt"
    PC = "pc"
    MM = "mm"
    CM = "cm"
    IN = "in"
    EM = "em"
    EX = "ex"
    PERCENT = "%"
    USER = ""
    PIXEL = "px"
    INCH = "in"

    def __str__(self) -> str:
        return self.value


_ABSOLUTE_PER_INCH: Final = {
    Unit.IN: 1.0,
    Unit.PT: PT_PER_INCH,
    Unit.PC: PC_PER_INCH,
    Unit.MM: MM_PER_INCH,
    Unit.CM: CM_PER_INCH,
}


@dataclass(frozen=True, slots=True)
class Length:
    """A number with an optional unit.

    Parameters
    ----------
    value : float
        The magnitude.
    unit : Unit, optional
        The unit; ``Unit.NONE`` means user units. Defaults to ``Unit.NONE``.

    See Also
    --------
    Unit : The available units.

    Examples
    --------
    >>> from svgwriter.attributes import Length, Unit
    >>> str(Length(2.5, Unit.MM))
    '2.5mm'
    >>> Length.parse("1in").to_user_units()
    96.0
    """

    value: float
    unit: Unit = Unit.NONE

    @overload
    @classmethod
    def parse(cls, text: str) -> Length: ...
    @overload
    @classmethod
    def parse(cls, text: float) -> Length: ...
    @overload
    @classmethod
    def parse(cls, text: Length) -> Length: ...
    @classmethod
    def parse(cls, text: str | float | Length) -> Length:
        """Parse length text such as ``"12.5mm"``.

        Numbers become unitless lengths and `Length` values pass through unchanged.

        Parameters
        ----------
        text : str or float or Length
            The value to convert.

        Returns
        -------
        Length
            The parsed length.

        Raises
        ------
        ValueError
            If the text is not a valid length.

        Examples
        --------
        >>> from svgwriter.attributes import Length
        >>> Length.parse("12.5mm")
        Length(value=12.5, unit=<Unit.MM: 'mm'>)
        >>> Length.parse(3).value
        3.0
        """
        if isinstance(text, Length):
            return text
        if isinstance(text, (int, float)):
            return cls(float(text))
        return _parse_cached(text)

    def to_user_units(
        self,
        *,
        dpi: float = DEFAULT_DPI,
        font_size: float = DEFAULT_FONT_SIZE,
        reference: float | None = None,
    ) -> float:
        """Convert to user units (pixels).

        Absolute units use the dots-per-inch setting; ``em`` and ``ex`` use the font size.

        Parameters
        ----------
        dpi : float, optional
            Pixels per inch for absolute units. Defaults to the library default DPI.
        font_size : float, optional
            Font size in pixels for ``em`` and ``ex``. Defaults to the library default font size.
        reference : float, optional
            The length that ``100%`` resolves to. Defaults to None.

        Returns
        -------
        float
            The length in user units.

        Raises
        ------
        ValueError
            If the length is a percentage and no `reference` is given.

        Examples
        --------
        >>> from svgwriter.attributes import Length, Unit
        >>> Length(1, Unit.IN).to_user_units(dpi=72)
        72.0
        >>> Length(50, Unit.PERCENT).to_user_units(reference=200)
        100.0
        """
        if self.unit in (Unit.NONE, Unit.PX):
            return self.value
        if self.unit is Unit.EM:
            return self.value * font_size
        if self.unit is Unit.EX:
            return self.value * font_size * EX_PER_EM
        if self.unit is Unit.PERCENT:
            if reference is None:
                raise ValueError("percentage lengths need a reference length")
            return self.value * reference / 100.0
        return self.value * dpi / _ABSOLUTE_PER_INCH[self.unit]

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize the length as attribute text.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places. Defaults to the library default precision.

        Returns
        -------
        str
            The number followed by its unit.

        Examples
        --------
        >>> from svgwriter.attributes import Length, Unit
        >>> Length(1.23456, Unit.PX).svg_value(2)
        '1.23px'
        """
        return format_number(self.value, precision) + self.unit.value

    def __str__(self) -> str:
        return self.svg_value()

    def __float__(self) -> float:
        return self.to_user_units()

    @property
    def absolute(self) -> bool:
        """Whether the unit converts to user units without context (not ``em``, ``ex`` or ``%``)."""
        return self.unit is Unit.NONE or self.unit is Unit.PX or self.unit in _ABSOLUTE_PER_INCH

    def to(self, unit: Unit | str) -> Length:
        """The same length in another absolute unit.

        Parameters
        ----------
        unit : Unit or str
            Target unit (``"mm"``, ``"in"``, ``"px"``, ``""`` for user units, ...).

        Returns
        -------
        Length
            The converted length, at 96 user units per inch as SVG defines.

        Raises
        ------
        ValueError
            If either unit is relative (``em``, ``ex``, ``%``).

        Examples
        --------
        >>> from svgwriter.attributes.length import inch
        >>> inch(1).to("mm")
        Length(value=25.4, unit=<Unit.MM: 'mm'>)
        """
        target = Unit(unit)
        if target is self.unit:
            return self
        if not (self.absolute and Length(0, target).absolute):
            raise ValueError(f"cannot convert {self.unit.value or 'user units'} to {target.value or 'user units'}: "
                             "relative units need a font size or reference length")
        pixels = self.to_user_units()
        per_inch = _ABSOLUTE_PER_INCH.get(target)
        return Length(pixels if per_inch is None else pixels / DEFAULT_DPI * per_inch, target)

    def _other(self, other: object, operation: str) -> Length:
        """*other* as a length in this length's unit, for addition and comparison."""
        if not isinstance(other, (Length, int, float, str)) or isinstance(other, bool):
            raise TypeError(f"cannot {operation} {type(other).__name__} and a length")
        value = Length.parse(other) if not isinstance(other, (int, float)) else Length(float(other), Unit.NONE)
        if value.unit is self.unit:
            return value
        if self.absolute and value.absolute:
            return value.to(self.unit)
        raise ValueError(f"cannot {operation} {self.unit.value or 'user units'} and "
                         f"{value.unit.value or 'user units'}: relative units only combine with themselves")

    def __add__(self, other: Length | float | str) -> Length:
        """``5mm + 1in`` or ``5mm + 3`` (plain numbers are user units); the result keeps this unit."""
        return Length(self.value + self._other(other, "add").value, self.unit)

    def __radd__(self, other: float) -> Length:
        return self + other

    def __sub__(self, other: Length | float | str) -> Length:
        return Length(self.value - self._other(other, "subtract").value, self.unit)

    def __rsub__(self, other: float) -> Length:
        return -self + other

    def __mul__(self, factor: float) -> Length:
        if isinstance(factor, Length):
            raise TypeError("a length times a length is an area, not a length; multiply by a number")
        return Length(self.value * factor, self.unit)

    __rmul__ = __mul__

    def __truediv__(self, other: float | Length) -> Any:
        """``length / number`` is a length; ``length / length`` is their plain ratio."""
        if isinstance(other, (Length, str)):
            return self.value / self._other(other, "divide").value
        return Length(self.value / other, self.unit)

    def __neg__(self) -> Length:
        return Length(-self.value, self.unit)

    def __abs__(self) -> Length:
        return Length(abs(self.value), self.unit)

    def __lt__(self, other: Length | float) -> bool:
        return self.value < self._other(other, "compare").value

    def __le__(self, other: Length | float) -> bool:
        return self.value <= self._other(other, "compare").value

    def __gt__(self, other: Length | float) -> bool:
        return self.value > self._other(other, "compare").value

    def __ge__(self, other: Length | float) -> bool:
        return self.value >= self._other(other, "compare").value


LengthLike: TypeAlias = Length | float | int | str


@lru_cache(maxsize=512)
def _parse_cached(text: str) -> Length:
    match = LENGTH_RE.match(text)
    if match is None:
        raise ValueError(f"invalid length: {text!r}")
    number, unit = match.groups()
    return Length(float(number), Unit(unit or ""))


class LengthUnit:
    """A unit you can call or multiply: ``mm(5)`` and ``5 * mm`` are both ``Length(5, Unit.MM)``.

    Parameters
    ----------
    unit : Unit
        The unit this factory produces.

    Examples
    --------
    >>> from svgwriter.attributes.length import inch, mm
    >>> str(5 * mm), str(inch(2) - 10 * mm)
    ('5mm', '1.6063in')
    """

    __slots__ = ("unit",)

    def __init__(self, unit: Unit) -> None:
        self.unit = unit

    def __call__(self, value: float) -> Length:
        return Length(float(value), self.unit)

    def __rmul__(self, value: float) -> Length:
        return Length(float(value), self.unit)

    def __repr__(self) -> str:
        return f"LengthUnit({self.unit.value!r})"


px = LengthUnit(Unit.PX)
"""Pixels (user units): ``px(5)`` or ``5 * px``."""
pt = LengthUnit(Unit.PT)
"""Points, 72 per inch: ``pt(5)`` or ``5 * pt``."""
pc = LengthUnit(Unit.PC)
"""Picas, 6 per inch: ``pc(5)`` or ``5 * pc``."""
mm = LengthUnit(Unit.MM)
"""Millimetres: ``mm(5)`` or ``5 * mm``."""
cm = LengthUnit(Unit.CM)
"""Centimetres: ``cm(5)`` or ``5 * cm``."""
inch = LengthUnit(Unit.IN)
"""Inches: ``inch(5)`` or ``5 * inch``."""
em = LengthUnit(Unit.EM)
"""Font-size multiples: ``em(5)`` or ``5 * em``."""
ex = LengthUnit(Unit.EX)
"""x-height multiples: ``ex(5)`` or ``5 * ex``."""
percent = LengthUnit(Unit.PERCENT)
"""Percentages: ``percent(5)`` or ``5 * percent``."""
