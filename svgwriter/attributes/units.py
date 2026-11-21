"""
Unit factories: ``mm(5)``, ``5 * mm``, ``length(5, "mm")``, ``deg(30)``, ``angle(30, "degrees")``.
"""

from __future__ import annotations

from .angle import Angle
from .length import Length, Unit

__all__ = [
    "AngleUnit",
    "LengthUnit",
    "angle",
    "cm",
    "deg",
    "em",
    "ex",
    "ft",
    "grad",
    "inch",
    "length",
    "m",
    "mm",
    "pc",
    "percent",
    "pt",
    "px",
    "q",
    "rad",
    "turn",
]


def length(value: float, unit: Unit | str = Unit.NONE) -> Length:
    """A length from a number and a unit, which may be spelled out.

    Parameters
    ----------
    value : float
        The magnitude.
    unit : Unit or str, optional
        ``"mm"``, ``"in"``, ``"millimetres"``, ``"inches"``, ``"m"``, ``"ft"``, ...;
        metres and feet are stored as millimetres and inches. Defaults to user units.

    Returns
    -------
    Length
        The length.

    Raises
    ------
    ValueError
        If the unit is unknown.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.length(2, "centimetres")), str(svg.length(0.5, "m"))
    ('2cm', '500mm')
    """
    return Length(float(value), unit)


def angle(value: float, unit: str = "deg") -> Angle:
    """An angle from a number and a unit, which may be spelled out.

    Parameters
    ----------
    value : float
        The magnitude.
    unit : str, optional
        ``"deg"``, ``"rad"``, ``"grad"``, ``"turn"`` or a name such as
        ``"degrees"``, ``"radians"``, ``"gon"``, ``"turns"``. Defaults to "deg".

    Returns
    -------
    Angle
        The angle.

    Raises
    ------
    ValueError
        If the unit is unknown.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.angle(0.25, "turns")), svg.angle(1, "radians").unit
    ('0.25turn', 'rad')
    """
    return Angle(float(value), unit)


class LengthUnit:
    """A unit you can call or multiply: ``mm(5)`` and ``5 * mm`` are both ``Length(5, Unit.MM)``.

    Parameters
    ----------
    unit : Unit or str
        The unit this factory produces; ``"m"`` and ``"ft"`` give millimetres and inches.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(5 * svg.mm), str(svg.inch(2) - 10 * svg.mm), str(svg.ft(1))
    ('5mm', '1.6063in', '12in')
    """

    __slots__ = ("unit",)

    def __init__(self, unit: Unit | str) -> None:
        self.unit = unit

    def __call__(self, value: float) -> Length:
        return Length(float(value), self.unit)

    def __rmul__(self, value: float) -> Length:
        return Length(float(value), self.unit)

    def __repr__(self) -> str:
        return f"LengthUnit({str(self.unit)!r})"


class AngleUnit:
    """A unit you can call or multiply: ``deg(30)`` and ``30 * deg`` are both ``Angle(30, "deg")``.

    Parameters
    ----------
    unit : str
        The unit this factory produces.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(30 * svg.deg), str(svg.turn(0.5))
    ('30deg', '0.5turn')
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


px = LengthUnit(Unit.PX)
"""Pixels (user units): ``px(5)`` or ``5 * px``."""
pt = LengthUnit(Unit.PT)
"""Points, 72 per inch: ``pt(5)`` or ``5 * pt``."""
pc = LengthUnit(Unit.PC)
"""Picas, 6 per inch: ``pc(5)`` or ``5 * pc``."""
mm = LengthUnit(Unit.MM)
"""Millimetres: ``mm(5)`` or ``5 * mm``."""
q = LengthUnit(Unit.Q)
"""Quarter millimetres, written ``Q``: ``q(5)`` or ``5 * q``."""
cm = LengthUnit(Unit.CM)
"""Centimetres: ``cm(5)`` or ``5 * cm``."""
m = LengthUnit("m")
"""Metres, written as millimetres: ``m(1)`` is ``1000mm``."""
inch = LengthUnit(Unit.IN)
"""Inches: ``inch(5)`` or ``5 * inch``."""
ft = LengthUnit("ft")
"""Feet, written as inches: ``ft(1)`` is ``12in``."""
em = LengthUnit(Unit.EM)
"""Font-size multiples: ``em(5)`` or ``5 * em``."""
ex = LengthUnit(Unit.EX)
"""x-height multiples: ``ex(5)`` or ``5 * ex``."""
percent = LengthUnit(Unit.PERCENT)
"""Percentages: ``percent(5)`` or ``5 * percent``."""

deg = AngleUnit("deg")
"""Degrees: ``deg(30)`` or ``30 * deg``."""
rad = AngleUnit("rad")
"""Radians: ``rad(1)`` or ``1 * rad``."""
grad = AngleUnit("grad")
"""Gradians, 400 per turn: ``grad(50)``."""
turn = AngleUnit("turn")
"""Full turns: ``turn(0.25)`` is 90 degrees."""
