"""
Numeric controls: sliders, a range slider and a number field, optionally in a length unit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import Any

from ..attributes import Length
from ..attributes.units import length
from ._constants import SLIDER_STEPS
from ._control import Control

__all__ = ["IntSlider", "Number", "RangeSlider", "Slider", "length_unit"]


def length_unit(units: str | None) -> str | None:
    """*units* when it names a length unit (``"mm"``, ``"pt"``, ...), else None (a label only)."""
    if not units:
        return None
    try:
        length(0, units)
    except ValueError:
        return None
    return units


def _number(value: Any, unit: str | None, integer: bool) -> float | int:
    if isinstance(value, Length):
        if unit is None or value.unit.value != length(0, unit).unit.value:
            raise ValueError(f"expected a number{f' in {unit}' if unit else ''}, got {value}")
        value = value.value
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"expected a number, got {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"expected a finite number, got {value}")
    if integer:
        if value != int(value):
            raise ValueError(f"expected a whole number, got {value}")
        return int(value)
    return float(value)


@dataclass(frozen=True, kw_only=True)
class _Numeric(Control):
    units: str | None = None
    format: str | None = None

    _integer = False

    def _bounded(self, value: Any) -> float | int:
        number = _number(value, length_unit(self.units), self._integer)
        low, high = getattr(self, "min", None), getattr(self, "max", None)
        if (low is not None and number < low) or (high is not None and number > high):
            raise ValueError(f"{number:g} is outside {low:g}..{high:g}" if low is not None and high is not None
                             else f"{number:g} is out of range")
        return number

    def argument(self, value: Any) -> Any:
        unit = length_unit(self.units)
        if unit is None:
            return value
        return tuple(length(part, unit) for part in value) if isinstance(value, tuple) else length(value, unit)

    def code(self, value: Any) -> str:
        unit = length_unit(self.units)
        if unit is None:
            return repr(value)
        parts = [f"svg.length({part!r}, {unit!r})" for part in (value if isinstance(value, tuple) else (value,))]
        return f"({', '.join(parts)})" if isinstance(value, tuple) else parts[0]

    def _one(self, value: float) -> str:
        if self.format is None:
            shown = f"{value:g}"
        else:
            shown = self.format.format(value) if "{" in self.format else format(value, self.format)
        return f"{shown} {self.units}" if self.units and length_unit(self.units) is None and len(self.units) > 1 \
            else f"{shown}{self.units or ''}"

    def text(self, value: Any) -> str:
        return " – ".join(self._one(part) for part in value) if isinstance(value, tuple) else self._one(value)


def _range(control: Any) -> None:
    low = _number(control.min, length_unit(control.units), control._integer)
    high = _number(control.max, length_unit(control.units), control._integer)
    if not low < high:
        raise ValueError(f"{type(control).__name__} needs min < max, got {low:g} and {high:g}")
    object.__setattr__(control, "min", low)
    object.__setattr__(control, "max", high)
    step = control.step if control.step is not None else (1 if control._integer else (high - low) / SLIDER_STEPS)
    step = _number(step, length_unit(control.units), control._integer)
    if step <= 0:
        raise ValueError(f"step must be positive, got {step:g}")
    object.__setattr__(control, "step", step)
    if control.value is not None:
        object.__setattr__(control, "value", control.check(control.value))


@dataclass(frozen=True)
class Slider(_Numeric):
    """A number between two ends.

    Parameters
    ----------
    min, max : float or Length
        The ends; lengths must be in `units`.
    step : float, optional
        The increment. Defaults to None, a hundredth of the range.
    value : float, optional
        The starting value. Defaults to None, the middle of the range.
    label : str, optional
        Shown beside the slider.
    units : str, optional
        Shown after the readout. A length unit (``"mm"``, ``"pt"``, ``"px"``, ...) also makes the
        drawing function receive a :class:`~svgwriter.Length` in that unit. Defaults to None.
    format : str, optional
        A format spec for the readout (``".1f"``, ``"{:.0f}°"``). Defaults to None (``:g``).

    Raises
    ------
    ValueError
        If ``min >= max``, the step is not positive or the value is out of range.

    See Also
    --------
    IntSlider : Whole numbers.
    RangeSlider : A pair of numbers.

    Examples
    --------
    >>> import svgwriter as svg
    >>> hue = svg.widgets.Slider(0, 360, step=1, format="{:.0f}°")
    >>> hue.initial, hue.text(120)
    (180.0, '120°')
    >>> svg.widgets.Slider(0, 10, units="mm").argument(2.5)
    Length(value=2.5, unit=<Unit.MM: 'mm'>)
    """

    min: float | Length
    max: float | Length
    step: float | None = None
    value: float | Length | None = None

    def __post_init__(self) -> None:
        _range(self)

    def _default(self) -> float | int:
        middle = (self.min + self.max) / 2  # type: ignore[operator]
        return int(middle) if self._integer else middle

    def check(self, value: Any) -> float | int:
        return self._bounded(value)


@dataclass(frozen=True)
class IntSlider(Slider):
    """A whole number between two ends; the step defaults to 1.

    Parameters
    ----------
    min, max : int
        The ends.
    step : int, optional
        The increment. Defaults to 1.
    value : int, optional
        The starting value. Defaults to the middle, rounded down.

    See Also
    --------
    Slider : Any number.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.widgets.IntSlider(1, 12).initial
    6
    """

    _integer = True


@dataclass(frozen=True)
class RangeSlider(_Numeric):
    """A pair of numbers ``(low, high)`` between two ends.

    Parameters
    ----------
    min, max : float
        The ends.
    step : float, optional
        The increment. Defaults to a hundredth of the range.
    value : tuple of float, optional
        The starting pair. Defaults to the whole range.
    integer : bool, optional
        Whole numbers only. Defaults to False.

    Examples
    --------
    >>> import svgwriter as svg
    >>> band = svg.widgets.RangeSlider(0, 100)
    >>> band.initial, band.check((20, 80))
    ((0.0, 100.0), (20.0, 80.0))
    """

    min: float
    max: float
    step: float | None = None
    value: tuple[float, float] | None = None
    integer: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "_integer", self.integer)
        _range(self)

    def _default(self) -> tuple[float, float]:
        return (self.min, self.max)

    def check(self, value: Any) -> tuple[float, float]:
        if isinstance(value, (str, bytes)) or not hasattr(value, "__len__") or len(value) != 2:
            raise TypeError(f"expected a (low, high) pair, got {value!r}")
        low, high = (self._bounded(part) for part in value)
        if low > high:
            raise ValueError(f"low {low:g} is above high {high:g}")
        return (low, high)


@dataclass(frozen=True)
class Number(_Numeric):
    """A typed-in number, optionally bounded; whole numbers when `value` is an int.

    Parameters
    ----------
    value : float, optional
        The starting value. Defaults to 0.
    min, max : float, optional
        Bounds. Defaults to None (unbounded).
    step : float, optional
        The increment of the arrows. Defaults to None (1).

    Examples
    --------
    >>> import svgwriter as svg
    >>> count = svg.widgets.Number(5, min=1)
    >>> count.check(8), count.text(8)
    (8, '8')
    """

    value: float = 0.0
    min: float | None = None
    max: float | None = None
    step: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "_integer", isinstance(self.value, int) and not isinstance(self.value, bool))
        if self.min is not None and self.max is not None and not self.min < self.max:
            raise ValueError(f"Number needs min < max, got {self.min:g} and {self.max:g}")
        object.__setattr__(self, "value", self.check(self.value))

    def _default(self) -> float | int:
        return self.value

    def check(self, value: Any) -> float | int:
        return self._bounded(value)
