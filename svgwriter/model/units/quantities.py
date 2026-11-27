"""
Products and quotients of lengths and angles: values carrying dimension exponents.

``mm(3) * mm(2)`` is an area, ``deg(90) / mm(5)`` an angle per length. Each
`Quantity` stores its magnitude in base units (user units for length, radians
for angle) with the exponents of both; once a calculation comes back to a plain
length, angle or number it is a `Length`, an `Angle` or a ``float`` again.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..._internal._constants import DEFAULT_PRECISION
from ..._internal._numbers import format_number
from ._constants import EQUAL_DIGITS, SUPERSCRIPTS

if TYPE_CHECKING:
    from .angles import Angle
    from .lengths import Length, Unit

__all__ = ["Quantity", "dimension_name"]


def dimension_name(length: int, angle: int) -> str:
    """How a dimension reads in messages: ``"length²"``, ``"length·angle⁻¹"``, ``"number"``.

    Parameters
    ----------
    length, angle : int
        The exponents of length and angle.

    Returns
    -------
    str
        The dimension written with superscript exponents.

    Examples
    --------
    >>> from svgwriter.model.units.quantities import dimension_name
    >>> dimension_name(2, 0), dimension_name(1, -1), dimension_name(0, 0)
    ('length²', 'length·angle⁻¹', 'number')
    """
    parts = [name + (str(power).translate(SUPERSCRIPTS) if power != 1 else "")
             for name, power in (("length", length), ("angle", angle)) if power]
    return "·".join(parts) or "number"


@dataclass(frozen=True, slots=True, eq=False)
class Quantity:
    """A value of dimension length^n · angle^m, the result of multiplying or dividing lengths and angles.

    Arithmetic works like a maths problem: products add exponents, quotients
    subtract them, and sums need equal dimensions. Results that are plain
    lengths, angles or numbers come back as `Length`, `Angle` or ``float``,
    in the unit of the first length or angle involved.

    Parameters
    ----------
    value : float
        Magnitude in user units^length · radians^angle.
    length, angle : int, optional
        Exponents of length and angle. Default to 0.
    length_unit : Unit, optional
        Unit used to show lengths and to give back a `Length`. Defaults to user units.
    angle_unit : str, optional
        Unit used to show angles and to give back an `Angle`. Defaults to "rad".

    See Also
    --------
    dimension_name : How a dimension reads.

    Examples
    --------
    >>> import svgwriter as svg
    >>> area = svg.mm(3) * svg.mm(2)
    >>> str(area), area.dimension
    ('6mm²', 'length²')
    >>> area / svg.mm(4)
    Length(value=1.5, unit=<Unit.MM: 'mm'>)
    >>> svg.mm(6) / svg.mm(3)
    2.0
    """

    value: float
    length: int = 0
    angle: int = 0
    length_unit: Unit | None = field(default=None, compare=False)
    angle_unit: str = field(default="rad", compare=False)

    @classmethod
    def of(cls, value: object) -> Quantity:
        """The quantity behind a length, angle, number or quantity.

        Parameters
        ----------
        value : Length, Angle, Quantity or float
            The value; lengths must be absolute (not ``em``, ``ex`` or ``%``).

        Returns
        -------
        Quantity
            The value in base units with its exponents.

        Raises
        ------
        TypeError
            If the value is not a number, length, angle or quantity.
        ValueError
            If a length is relative.

        Examples
        --------
        >>> import svgwriter as svg
        >>> Quantity.of(svg.inch(1)).value
        96.0
        """
        from .angles import Angle
        from .lengths import Length

        if isinstance(value, Quantity):
            return value
        if isinstance(value, Length):
            if not value.absolute:
                raise ValueError(f"{value.unit.value} lengths need a font size or reference length to multiply; "
                                 "convert them with to_user_units() first")
            return cls(value.to_user_units(), 1, 0, value.unit)
        if isinstance(value, Angle):
            return cls(value.radians, 0, 1, angle_unit=value.unit)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return cls(float(value))
        raise TypeError(f"cannot combine {type(value).__name__} with lengths and angles")

    @property
    def dimension(self) -> str:
        """The dimension as text, such as ``"length²"``."""
        return dimension_name(self.length, self.angle)

    def _scale(self) -> float:
        from .angles import Angle
        from .lengths import Length

        unit_length = Length(1, self.length_unit).to_user_units() if self.length_unit is not None else 1.0
        return unit_length ** self.length * Angle(1, self.angle_unit).radians ** self.angle

    def simplify(self) -> Quantity | Length | Angle | float:
        """This value as a `Length`, `Angle` or ``float`` when its dimension allows.

        Returns
        -------
        Quantity, Length, Angle or float
            The simplest type for the dimension.

        Examples
        --------
        >>> Quantity(2.0, 0, 0).simplify()
        2.0
        """
        from .angles import Angle
        from .lengths import Length, Unit

        if (self.length, self.angle) == (0, 0):
            return self.value
        if (self.length, self.angle) == (1, 0):
            return Length(self.value).to(self.length_unit or Unit.NONE)
        if (self.length, self.angle) == (0, 1):
            return Angle(math.degrees(self.value)).to(self.angle_unit)
        return self

    def _combine(self, other: object, sign: int) -> Any:
        try:
            right = Quantity.of(other)
        except TypeError:
            return NotImplemented
        value = self.value * right.value if sign > 0 else self.value / right.value
        return Quantity(value, self.length + sign * right.length, self.angle + sign * right.angle,
                        self.length_unit or right.length_unit,
                        self.angle_unit if self.angle else right.angle_unit).simplify()

    def _same(self, other: object, operation: str) -> Quantity:
        right = Quantity.of(other)
        if (right.length, right.angle) != (self.length, self.angle):
            raise TypeError(f"cannot {operation} {self.dimension} and {right.dimension}")
        return right

    def __mul__(self, other: object) -> Any:
        return self._combine(other, 1)

    __rmul__ = __mul__

    def __truediv__(self, other: object) -> Any:
        return self._combine(other, -1)

    def __rtruediv__(self, other: object) -> Any:
        return Quantity.of(other)._combine(self, -1)

    def __pow__(self, power: int) -> Any:
        return Quantity(self.value ** power, self.length * power, self.angle * power,
                        self.length_unit, self.angle_unit).simplify()

    def __add__(self, other: object) -> Any:
        return Quantity(self.value + self._same(other, "add").value, self.length, self.angle,
                        self.length_unit, self.angle_unit).simplify()

    __radd__ = __add__

    def __sub__(self, other: object) -> Any:
        return self + -Quantity.of(other)

    def __rsub__(self, other: object) -> Any:
        return -self + other

    def __neg__(self) -> Quantity:
        return Quantity(-self.value, self.length, self.angle, self.length_unit, self.angle_unit)

    def __abs__(self) -> Quantity:
        return Quantity(abs(self.value), self.length, self.angle, self.length_unit, self.angle_unit)

    def __eq__(self, other: object) -> bool:
        """Equal dimension and magnitude, like `Length` and plain numbers."""
        try:
            right = Quantity.of(other)
        except (TypeError, ValueError):
            return NotImplemented
        return (right.length, right.angle) == (self.length, self.angle) and round(right.value, EQUAL_DIGITS) == round(self.value, EQUAL_DIGITS)

    def __hash__(self) -> int:
        return hash(round(self.value, EQUAL_DIGITS))

    def __lt__(self, other: object) -> bool:
        return self.value < self._same(other, "compare").value

    def __le__(self, other: object) -> bool:
        return self.value <= self._same(other, "compare").value

    def __gt__(self, other: object) -> bool:
        return self.value > self._same(other, "compare").value

    def __ge__(self, other: object) -> bool:
        return self.value >= self._same(other, "compare").value

    def __str__(self) -> str:
        units = [suffix + (str(power).translate(SUPERSCRIPTS) if power != 1 else "")
                 for suffix, power in (((self.length_unit.value if self.length_unit else "") or "px", self.length),
                                       (self.angle_unit, self.angle)) if power]
        return format_number(self.value / self._scale(), DEFAULT_PRECISION) + "·".join(units)
