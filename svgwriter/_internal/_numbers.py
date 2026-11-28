"""
Number formatting for attribute values.
"""

from __future__ import annotations

import math

from ._constants import DEFAULT_PRECISION, INDEFINITE

__all__ = ["format_number", "number_values"]


def format_number(value: float, precision: int = DEFAULT_PRECISION) -> str:
    """Format *value* with at most *precision* decimals and no trailing zeros."""
    if math.isinf(value):
        if value > 0:
            return INDEFINITE
        raise ValueError("negative infinity has no SVG representation")
    if math.isnan(value):
        raise ValueError("NaN has no SVG representation")
    if float(value).is_integer():
        return str(int(value))
    text = f"{value:.{precision}f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def number_values(value: object) -> list[float]:
    """Floats from an SVG number list: ``"1 2,3"``, a list or tuple of numbers, or None (empty).

    Examples
    --------
    >>> number_values("1 2,3.5"), number_values((1, 2)), number_values(None)
    ([1.0, 2.0, 3.5], [1.0, 2.0], [])
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [float(item) for item in value]
    return [float(item) for item in str(value).replace(",", " ").split()]
