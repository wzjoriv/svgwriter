"""
The functions theme expressions may call: a fixed table of names mapped to explicit callables.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, TypeAlias

from ..color.color import Color, parse_color
from ._constants import CONDITIONAL, MAX_ARGUMENTS, MAX_ROUND_DIGITS
from ._lexer import ExpressionError

__all__ = ["FUNCTIONS", "Function", "Value", "arity", "kind"]

Value: TypeAlias = "bool | int | float | str | Color"
"""What an expression produces: a condition, a number, text or a color."""


def kind(value: Value) -> str:
    """The name of a value's type in messages: condition, number, text or color."""
    if isinstance(value, bool):
        return "condition"
    if isinstance(value, (int, float)):
        return "number"
    return "color" if isinstance(value, Color) else "text"


def _color(args: Sequence[Value], index: int) -> Color:
    value = args[index]
    if isinstance(value, Color):
        return value
    if isinstance(value, str):
        try:
            return parse_color(value)
        except ValueError:
            pass
    raise ExpressionError(f"argument {index + 1} must be a color, got {kind(value)}")


def _number(args: Sequence[Value], index: int) -> float:
    value = args[index]
    if kind(value) != "number":
        raise ExpressionError(f"argument {index + 1} must be a number, got {kind(value)}")
    return value  # type: ignore[return-value]


def _fraction(args: Sequence[Value], index: int) -> float:
    value = _number(args, index)
    if not 0 <= value <= 1:
        raise ExpressionError(f"argument {index + 1} must be between 0 and 1, got {value:g}")
    return value


def _text(args: Sequence[Value], index: int) -> str:
    value = args[index]
    if kind(value) != "text":
        raise ExpressionError(f"argument {index + 1} must be text, got {kind(value)}")
    return value  # type: ignore[return-value]


def _numbers(args: Sequence[Value]) -> list[float]:
    return [_number(args, i) for i in range(len(args))]


def _mix(args: Sequence[Value]) -> Color:
    extras = [read(args, i) for i, read in ((2, _fraction), (3, _text)) if i < len(args)]
    return _color(args, 0).mix(_color(args, 1), *extras)  # type: ignore[arg-type]


def _readable(args: Sequence[Value]) -> Color:
    return _color(args, 0).readable(*(_color(args, i) for i in range(1, len(args))))


def _clamp(args: Sequence[Value]) -> float:
    value, low, high = _numbers(args)
    if low > high:
        raise ExpressionError(f"the lower bound {low:g} is above the upper bound {high:g}")
    return min(max(value, low), high)


def _round(args: Sequence[Value]) -> float:
    if len(args) == 1:
        return round(_number(args, 0))
    digits = _number(args, 1)
    if digits != int(digits) or not 0 <= digits <= MAX_ROUND_DIGITS:
        raise ExpressionError(f"argument 2 must be a whole number from 0 to {MAX_ROUND_DIGITS}")
    return round(_number(args, 0), int(digits))


@dataclass(frozen=True)
class Function:
    """A callable of the expression language: how many arguments it takes and what it does."""

    minimum: int
    maximum: int
    call: Callable[[Sequence[Value]], Value]


FUNCTIONS: Final[Mapping[str, Function]] = MappingProxyType({
    "lighten": Function(2, 2, lambda a: _color(a, 0).lighten(_fraction(a, 1))),
    "darken": Function(2, 2, lambda a: _color(a, 0).darken(_fraction(a, 1))),
    "mix": Function(2, 4, _mix),
    "alpha": Function(2, 2, lambda a: _color(a, 0).with_alpha(_fraction(a, 1))),
    "saturate": Function(2, 2, lambda a: _color(a, 0).saturate(_fraction(a, 1))),
    "desaturate": Function(2, 2, lambda a: _color(a, 0).desaturate(_fraction(a, 1))),
    "hue_shift": Function(2, 2, lambda a: _color(a, 0).hue_shift(_number(a, 1))),
    "complement": Function(1, 1, lambda a: _color(a, 0).complement()),
    "grayscale": Function(1, 1, lambda a: _color(a, 0).grayscale()),
    "invert": Function(1, 1, lambda a: _color(a, 0).invert()),
    "luminance": Function(1, 1, lambda a: _color(a, 0).luminance),
    "contrast": Function(2, 2, lambda a: _color(a, 0).contrast(_color(a, 1))),
    "is_dark": Function(1, 1, lambda a: _color(a, 0).is_dark),
    "is_light": Function(1, 1, lambda a: _color(a, 0).is_light),
    "readable": Function(1, 3, _readable),
    "min": Function(1, MAX_ARGUMENTS, lambda a: min(_numbers(a))),
    "max": Function(1, MAX_ARGUMENTS, lambda a: max(_numbers(a))),
    "clamp": Function(3, 3, _clamp),
    "round": Function(1, 2, _round),
})


def arity(name: str) -> tuple[int, int] | None:
    """The fewest and most arguments of function *name*, or None if there is no such function."""
    if name == CONDITIONAL:
        return (3, 3)
    function = FUNCTIONS.get(name)
    return None if function is None else (function.minimum, function.maximum)
