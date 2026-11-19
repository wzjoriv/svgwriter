"""Number formatting for attribute values."""

from __future__ import annotations

import math

from ._constants import DEFAULT_PRECISION, INDEFINITE

__all__ = ["format_number"]


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
