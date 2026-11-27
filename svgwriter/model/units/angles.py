"""
Angles with units: degrees, radians, gradians and turns, converted and combined freely.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..._internal._constants import DEFAULT_PRECISION
from ..._internal._numbers import format_number
from ._constants import (
    ANGLE_RE,
    ANGLE_SPELLINGS,
    DEGREES_PER,
    EQUAL_DIGITS,
    FULL_TURN_DEGREES,
    HALF_TURN_DEGREES,
)
from .quantities import Quantity

if TYPE_CHECKING:
    from .lengths import Length

__all__ = ["Angle"]


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


@dataclass(frozen=True, slots=True, eq=False)
class Angle:
    """An angle with a unit; ``float(angle)`` is degrees, as every svgwriter rotation expects.

    Any two angles add, subtract and compare whatever their units; plain
    numbers count as degrees, as in SVG. Positive angles turn from +x towards
    +y, which is clockwise on screen. Multiplying or dividing by lengths and
    angles gives a `~svgwriter.model.units.quantities.Quantity`.

    Parameters
    ----------
    value : float
        The magnitude.
    unit : str, optional
        ``"deg"``, ``"rad"``, ``"grad"`` or ``"turn"``, or a spelled-out name
        (``"degrees"``, ``"radians"``, ``"gon"``, ``"turns"``, ...). Defaults to "deg".

    Examples
    --------
    >>> import svgwriter as svg
    >>> float(svg.turn(0.25)), str(svg.rad(1) + 30)
    (90.0, '1.5236rad')
    >>> svg.rect(0, 0, 4, 2).rotate(svg.rad(math.pi / 2)).matrix.decompose()[2]
    90.0
    >>> str(Angle(2, "radians"))
    '2rad'
    """

    value: float
    unit: str = "deg"

    def __post_init__(self) -> None:
        unit = ANGLE_SPELLINGS.get(str(self.unit).lower())
        if unit is None:
            raise ValueError(f"unknown angle unit {self.unit!r}; use one of {', '.join(DEGREES_PER)}")
        object.__setattr__(self, "unit", unit)

    @classmethod
    def parse(cls, text: str | float | Angle) -> Angle:
        """An angle from ``"45deg"``, ``"1.2rad"``, ``"0.5turn"``, a number (degrees) or an angle.

        Parameters
        ----------
        text : str, float or Angle
            The value.

        Returns
        -------
        Angle
            The parsed angle.

        Raises
        ------
        ValueError
            If the text is not an angle.
        TypeError
            If the value is a length or another non-angle quantity.

        Examples
        --------
        >>> Angle.parse("0.5turn").degrees
        180.0
        """
        if isinstance(text, Angle):
            return text
        if _number(text):
            return cls(float(text))  # type: ignore[arg-type]
        if not isinstance(text, str):
            dimension = text.dimension if isinstance(text, Quantity) else "length"
            raise TypeError(f"needs an angle, got {dimension}")
        match = ANGLE_RE.match(text)
        if match is None:
            raise ValueError(f"invalid angle: {text!r}")
        return cls(float(match.group(1)), match.group(2) or "deg")

    @property
    def degrees(self) -> float:
        """The angle in degrees."""
        return self.value * DEGREES_PER[self.unit]

    @property
    def radians(self) -> float:
        """The angle in radians."""
        return math.radians(self.degrees)

    def to(self, unit: str) -> Angle:
        """The same angle in another unit (``"deg"``, ``"rad"``, ``"grad"``, ``"turn"`` or a spelled-out name)."""
        unit = Angle(0, unit).unit
        return Angle(self.degrees / DEGREES_PER[unit], unit)

    def _degrees_as_self(self, degrees: float) -> Angle:
        return Angle(degrees / DEGREES_PER[self.unit], self.unit)

    def wrap(self) -> Angle:
        """The same direction within one turn, from 0 up to (not including) a full turn.

        Returns
        -------
        Angle
            The wrapped angle, in this angle's unit.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.deg(-90).wrap()), str(svg.turn(1.25).wrap())
        ('270deg', '0.25turn')
        """
        return self._degrees_as_self(self.degrees % FULL_TURN_DEGREES)

    def diff(self, other: Angle | float, ccw: bool | None = None) -> Angle:
        """The turn from this angle to *other*, the short way round unless a direction is given.

        Parameters
        ----------
        other : Angle or float
            The target angle; numbers are degrees.
        ccw : bool, optional
            None takes the shorter arc (at most half a turn either way);
            True turns counter-clockwise on screen (negative angles) and False
            clockwise (positive angles). Defaults to None.

        Returns
        -------
        Angle
            The signed turn, in this angle's unit.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.deg(350).diff(10)), str(svg.deg(350).diff(10, ccw=True))
        ('20deg', '-340deg')
        """
        turn = (Angle.parse(other).degrees - self.degrees) % FULL_TURN_DEGREES
        if ccw is None:
            turn = turn - FULL_TURN_DEGREES if turn > HALF_TURN_DEGREES else turn
        elif ccw:
            turn = turn - FULL_TURN_DEGREES if turn else 0.0
        return self._degrees_as_self(turn)

    def lerp(self, other: Angle | float, t: float, ccw: bool | None = None) -> Angle:
        """The angle a fraction *t* of the way to *other*, turning as `diff` does.

        Parameters
        ----------
        other : Angle or float
            The end angle; numbers are degrees.
        t : float
            0 gives this angle, 1 gives *other* (as the same direction).
        ccw : bool, optional
            Turning direction, as in `diff`. Defaults to None (the shorter arc).

        Returns
        -------
        Angle
            The blended angle, in this angle's unit.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.deg(350).lerp(10, 0.5))
        '360deg'
        """
        return self + self.diff(other, ccw) * t

    def clamp(self, low: Angle | float, high: Angle | float, circular: bool = False) -> Angle:
        """This angle limited to the range from *low* to *high*.

        Parameters
        ----------
        low, high : Angle or float
            The limits; numbers are degrees.
        circular : bool, optional
            Treat the range as the arc swept clockwise from *low* to *high*,
            so directions are compared modulo a turn and an angle outside snaps
            to the nearer end. Defaults to False (plain numeric clamping).

        Returns
        -------
        Angle
            The limited angle, in this angle's unit.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.deg(100).clamp(0, 90)), str(svg.deg(5).clamp(350, 20, circular=True))
        ('90deg', '5deg')
        >>> str(svg.deg(100).clamp(350, 20, circular=True))
        '20deg'
        """
        start, end = Angle.parse(low), Angle.parse(high)
        if not circular:
            return self._degrees_as_self(min(max(self.degrees, start.degrees), end.degrees))
        width = start.diff(end, ccw=False).degrees
        if start.diff(self, ccw=False).degrees <= width:
            return self
        before, after = abs(self.diff(start).degrees), abs(self.diff(end).degrees)
        return start.to(self.unit) if before < after else end.to(self.unit)

    def sin(self) -> float:
        """The sine of this angle."""
        return math.sin(self.radians)

    def cos(self) -> float:
        """The cosine of this angle."""
        return math.cos(self.radians)

    def tan(self) -> float:
        """The tangent of this angle."""
        return math.tan(self.radians)

    def arclength(self, radius: Length | float) -> Length:
        """Length of the arc this angle sweeps on a circle of *radius*.

        Parameters
        ----------
        radius : Length or float
            The radius; numbers are user units.

        Returns
        -------
        Length
            The arc length, in the radius's unit.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.turn(0.5).arclength(svg.mm(10)))
        '31.4159mm'
        """
        from .lengths import Length

        return Length.parse(radius) * abs(self.radians)

    def _value(self, other: object) -> float:
        if isinstance(other, bool) or not isinstance(other, (Angle, int, float, str)):
            raise TypeError(f"cannot combine an angle and {type(other).__name__}")
        return Angle.parse(other).degrees / DEGREES_PER[self.unit]

    def __add__(self, other: Angle | float) -> Angle:
        return Angle(self.value + self._value(other), self.unit)

    __radd__ = __add__

    def __sub__(self, other: Angle | float) -> Angle:
        return Angle(self.value - self._value(other), self.unit)

    def __rsub__(self, other: float) -> Angle:
        return Angle(self._value(other) - self.value, self.unit)

    def __mul__(self, other: object) -> Any:
        """``angle * number`` is an angle; a length or angle factor gives a `Quantity`."""
        if _number(other):
            return Angle(self.value * other, self.unit)  # type: ignore[operator]
        return Quantity.of(self) * other

    __rmul__ = __mul__

    def __truediv__(self, other: object) -> Any:
        """``angle / number`` is an angle; ``angle / angle`` is their plain ratio."""
        if isinstance(other, Angle):
            return self.degrees / other.degrees
        if _number(other):
            return Angle(self.value / other, self.unit)  # type: ignore[operator]
        return Quantity.of(self) / other

    def __rtruediv__(self, other: object) -> Any:
        return Quantity.of(other) / self

    def __pow__(self, power: int) -> Any:
        return Quantity.of(self) ** power

    def __neg__(self) -> Angle:
        return Angle(-self.value, self.unit)

    def __abs__(self) -> Angle:
        return Angle(abs(self.value), self.unit)

    def __float__(self) -> float:
        return self.degrees

    def __eq__(self, other: object) -> bool:
        """Equal turns of any unit; plain numbers are degrees."""
        if isinstance(other, bool) or not isinstance(other, (Angle, int, float)):
            return NotImplemented
        return round(self.degrees, EQUAL_DIGITS) == round(other.degrees if isinstance(other, Angle) else float(other), EQUAL_DIGITS)

    def __hash__(self) -> int:
        return hash(round(self.degrees, EQUAL_DIGITS))

    def __lt__(self, other: Angle | float) -> bool:
        return self.value < self._value(other)

    def __le__(self, other: Angle | float) -> bool:
        return self.value <= self._value(other)

    def __gt__(self, other: Angle | float) -> bool:
        return self.value > self._value(other)

    def __ge__(self, other: Angle | float) -> bool:
        return self.value >= self._value(other)

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """The angle as SVG writes it: degrees, without a unit."""
        return format_number(self.degrees, precision)

    def __str__(self) -> str:
        return format_number(self.value, DEFAULT_PRECISION) + self.unit
