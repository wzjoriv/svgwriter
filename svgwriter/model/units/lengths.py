"""
Lengths with units (``10``, ``2.5mm``, ``50%``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Final, TypeAlias, overload

from ..._internal._constants import (
    CM_PER_INCH,
    DEFAULT_FONT_SIZE,
    DEFAULT_PRECISION,
    EX_PER_EM,
    MM_PER_INCH,
    PC_PER_INCH,
    PT_PER_INCH,
    PX_PER_INCH,
    Q_PER_INCH,
)
from ..._internal._enums import Keyword
from ..._internal._numbers import format_number
from ._constants import EQUAL_DIGITS, LENGTH_RE, LENGTH_SCALES, LENGTH_SPELLINGS
from .quantities import Quantity

if TYPE_CHECKING:
    from ..transform.matrix import Point
    from .angles import Angle

__all__ = ["Length", "LengthLike", "Unit"]


class Unit(Keyword):
    """Length units: SVG 1.1's plus CSS's ``Q`` (quarter millimetres).

    ``NONE`` (also ``USER``) means user units. ``PIXEL`` and ``INCH`` are
    aliases of ``PX`` and ``IN``. ``str(unit)`` gives the suffix as written in SVG.

    See Also
    --------
    Length : A value with a unit.

    Examples
    --------
    >>> from svgwriter.model.units import Unit
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
    Q = "Q"
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
    Unit.Q: Q_PER_INCH,
}


@dataclass(frozen=True, slots=True, eq=False)
class Length:
    """A number with an optional unit.

    The unit may be spelled out (``"millimetres"``, ``"inches"``); metres and
    feet are accepted too and stored as millimetres and inches, since SVG has
    no such units. Multiplying or dividing by other lengths and angles gives a
    `~svgwriter.model.units.quantities.Quantity` (an area, for instance) that turns
    back into a length when the dimensions cancel.

    Parameters
    ----------
    value : float
        The magnitude.
    unit : Unit or str, optional
        The unit; ``Unit.NONE`` means user units. Defaults to ``Unit.NONE``.

    See Also
    --------
    Unit : The available units.

    Examples
    --------
    >>> from svgwriter.model.units import Length, Unit
    >>> str(Length(2.5, Unit.MM))
    '2.5mm'
    >>> Length.parse("1in").to_user_units()
    96.0
    >>> str(Length(1.5, "metres")), str(Length(2, "ft"))
    ('1500mm', '24in')
    >>> Length(96) == 96, Length(1, "in") == 96, Length(1, "em") == 16
    (True, True, False)
    """

    value: float
    unit: Unit = Unit.NONE

    def __post_init__(self) -> None:
        if isinstance(self.unit, Unit):
            return
        spelling = LENGTH_SPELLINGS.get(str(self.unit).lower())
        if spelling is None:
            raise ValueError(f"unknown length unit {self.unit!r}")
        suffix, scale = LENGTH_SCALES.get(spelling, (spelling, 1.0))
        object.__setattr__(self, "value", self.value * scale)
        object.__setattr__(self, "unit", Unit(suffix))

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
        TypeError
            If the value is an angle or another non-length quantity.

        Examples
        --------
        >>> from svgwriter.model.units import Length
        >>> Length.parse("12.5mm")
        Length(value=12.5, unit=<Unit.MM: 'mm'>)
        >>> Length.parse(3).value
        3.0
        """
        if isinstance(text, Length):
            return text
        if isinstance(text, (int, float)):
            return cls(float(text))
        if not isinstance(text, str):
            raise TypeError(f"needs a length, got {_dimension(text)}")
        return _parse_cached(text)

    def to_user_units(
        self,
        *,
        units_per_inch: float = PX_PER_INCH,
        font_size: float = DEFAULT_FONT_SIZE,
        reference: float | None = None,
    ) -> float:
        """Convert to user units (pixels).

        Absolute units use `units_per_inch`; ``em`` and ``ex`` use the font size.

        Parameters
        ----------
        units_per_inch : float, optional
            User units per inch for absolute units. Defaults to 96, as SVG defines.
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
        >>> from svgwriter.model.units import Length, Unit
        >>> Length(1, Unit.IN).to_user_units(units_per_inch=72)
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
        return self.value * units_per_inch / _ABSOLUTE_PER_INCH[self.unit]

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
        >>> from svgwriter.model.units import Length, Unit
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
        >>> import svgwriter as svg
        >>> svg.inch(1).to("mm")
        Length(value=25.4, unit=<Unit.MM: 'mm'>)
        """
        target = Length(0, unit).unit
        if target is self.unit:
            return self
        if not (self.absolute and Length(0, target).absolute):
            raise ValueError(f"cannot convert {self.unit.value or 'user units'} to {target.value or 'user units'}: "
                             "relative units need a font size or reference length")
        pixels = self.to_user_units()
        per_inch = _ABSOLUTE_PER_INCH.get(target)
        return Length(pixels if per_inch is None else pixels / PX_PER_INCH * per_inch, target)

    def _other(self, other: object, operation: str) -> Length:
        """*other* as a length in this length's unit, for addition and comparison."""
        if not isinstance(other, (Length, int, float, str)) or isinstance(other, bool):
            raise TypeError(f"cannot {operation} {_dimension(other)} and a length")
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

    def __mul__(self, other: object) -> Any:
        """``length * number`` is a length; a length or angle factor gives a `Quantity` such as an area."""
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return Length(self.value * other, self.unit)
        return Quantity.of(self) * other

    __rmul__ = __mul__

    def __truediv__(self, other: object) -> Any:
        """``length / number`` is a length; ``length / length`` is their plain ratio."""
        if isinstance(other, (Length, str)):
            return self.value / self._other(other, "divide").value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return Length(self.value / other, self.unit)
        return Quantity.of(self) / other

    def __rtruediv__(self, other: object) -> Any:
        return Quantity.of(other) / self

    def __pow__(self, power: int) -> Any:
        return Quantity.of(self) ** power

    def __matmul__(self, angle: Angle | float) -> Point:
        """``distance @ angle``: the point at that distance from the origin, in that direction.

        Plain numbers are degrees; positive angles turn from +x towards +y.

        Examples
        --------
        >>> import svgwriter as svg
        >>> p = svg.px(2) @ svg.deg(90)
        >>> round(p.x, 9), p.y
        (0.0, 2.0)
        """
        from ..transform.matrix import Point
        from .angles import Angle

        direction = Angle.parse(angle)
        radius = self.to_user_units()
        return Point(radius * math.cos(direction.radians), radius * math.sin(direction.radians))

    def __neg__(self) -> Length:
        return Length(-self.value, self.unit)

    def __abs__(self) -> Length:
        return Length(abs(self.value), self.unit)

    def __eq__(self, other: object) -> bool:
        """Equal physical lengths; plain numbers are user units, and relative units only equal themselves."""
        if isinstance(other, bool) or not isinstance(other, (Length, int, float)):
            return NotImplemented
        right = other if isinstance(other, Length) else Length(float(other))
        if self.absolute and right.absolute:
            return round(self.to_user_units(), EQUAL_DIGITS) == round(right.to_user_units(), EQUAL_DIGITS)
        return self.value == right.value and self.unit is right.unit

    def __hash__(self) -> int:
        return hash(round(self.to_user_units(), EQUAL_DIGITS)) if self.absolute else hash((self.value, self.unit))

    def __lt__(self, other: Length | float) -> bool:
        return self.value < self._other(other, "compare").value

    def __le__(self, other: Length | float) -> bool:
        return self.value <= self._other(other, "compare").value

    def __gt__(self, other: Length | float) -> bool:
        return self.value > self._other(other, "compare").value

    def __ge__(self, other: Length | float) -> bool:
        return self.value >= self._other(other, "compare").value


LengthLike: TypeAlias = Length | float | int | str


def _dimension(value: object) -> str:
    from .angles import Angle

    if isinstance(value, Quantity):
        return value.dimension
    return "angle" if isinstance(value, Angle) else type(value).__name__


@lru_cache(maxsize=512)
def _parse_cached(text: str) -> Length:
    match = LENGTH_RE.match(text)
    if match is None:
        raise ValueError(f"invalid length: {text!r}")
    number, unit = match.groups()
    return Length(float(number), unit or "")
