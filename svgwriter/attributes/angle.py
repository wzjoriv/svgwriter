"""
Angles with units: degrees, radians, gradians and turns, converted and combined freely.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Final

from .._internal._constants import DEFAULT_PRECISION
from .._internal._numbers import format_number

__all__ = ["Angle", "AngleUnit", "deg", "grad", "rad", "turn"]

DEGREES_PER: Final = {"deg": 1.0, "rad": 180.0 / math.pi, "grad": 0.9, "turn": 360.0}
_ANGLE_RE: Final = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*(deg|rad|grad|turn)?\s*$")


@dataclass(frozen=True, slots=True)
class Angle:
    """An angle with a unit; ``float(angle)`` is degrees, as every svgwriter rotation expects.

    Any two angles add, subtract and compare whatever their units; plain
    numbers count as degrees, as in SVG.

    Parameters
    ----------
    value : float
        The magnitude.
    unit : {"deg", "rad", "grad", "turn"}, optional
        The unit. Defaults to "deg".

    Examples
    --------
    >>> import svgwriter as svg
    >>> float(svg.turn(0.25)), str(svg.rad(1) + 30)
    (90.0, '1.5236rad')
    >>> svg.rect(0, 0, 4, 2).rotate(svg.rad(math.pi / 2)).t.decompose()[2]
    90.0
    """

    value: float
    unit: str = "deg"

    def __post_init__(self) -> None:
        if self.unit not in DEGREES_PER:
            raise ValueError(f"unknown angle unit {self.unit!r}; use one of {', '.join(DEGREES_PER)}")

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

        Examples
        --------
        >>> Angle.parse("0.5turn").degrees
        180.0
        """
        if isinstance(text, Angle):
            return text
        if isinstance(text, (int, float)):
            return cls(float(text))
        match = _ANGLE_RE.match(str(text))
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
        """The same angle in another unit (``"deg"``, ``"rad"``, ``"grad"``, ``"turn"``)."""
        return Angle(self.degrees / DEGREES_PER[unit], unit)

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

    def __mul__(self, factor: float) -> Angle:
        if isinstance(factor, Angle):
            raise TypeError("an angle times an angle is not an angle; multiply by a number")
        return Angle(self.value * factor, self.unit)

    __rmul__ = __mul__

    def __truediv__(self, other: float | Angle) -> Any:
        """``angle / number`` is an angle; ``angle / angle`` is their plain ratio."""
        if isinstance(other, Angle):
            return self.degrees / other.degrees
        return Angle(self.value / other, self.unit)

    def __neg__(self) -> Angle:
        return Angle(-self.value, self.unit)

    def __float__(self) -> float:
        return self.degrees

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


class AngleUnit:
    """A unit you can call or multiply: ``deg(30)`` and ``30 * deg`` are both ``Angle(30, "deg")``.

    Parameters
    ----------
    unit : str
        The unit this factory produces.
    """

    __slots__ = ("unit",)

    def __init__(self, unit: str) -> None:
        self.unit = unit

    def __call__(self, value: float) -> Angle:
        return Angle(float(value), self.unit)

    def __rmul__(self, value: float) -> Angle:
        return Angle(float(value), self.unit)

    def __repr__(self) -> str:
        return f"AngleUnit({self.unit!r})"


deg = AngleUnit("deg")
"""Degrees: ``deg(30)`` or ``30 * deg``."""
rad = AngleUnit("rad")
"""Radians: ``rad(1)`` or ``1 * rad``."""
grad = AngleUnit("grad")
"""Gradians, 400 per turn: ``grad(50)``."""
turn = AngleUnit("turn")
"""Full turns: ``turn(0.25)`` is 90 degrees."""
