"""
Column text: numbers, strings, transforms and point lists formatted for many items at once.
"""

from __future__ import annotations

import numpy as np

from ..._internal._escape import escape_attribute
from ..._internal._numbers import format_number
from ..attributes.values import format_value
from ._constants import EXACT_INTEGER

__all__ = ["constant", "matrix_texts", "number_texts", "point_texts", "value_texts"]


def constant(column: np.ndarray) -> bool:
    """Whether every item of *column* is the same value without looking (a broadcast scalar)."""
    return column.ndim == 1 and column.strides[0] == 0


def number_texts(column: np.ndarray, precision: int) -> list[str]:
    """Each number written as :func:`format_number` would, at most *precision* decimals.

    Raises
    ------
    ValueError
        If a value is NaN or negative infinity.
    """
    values = np.asarray(column, dtype=float)
    if not np.isfinite(values).all():
        return [format_number(value, precision) for value in values.tolist()]
    if np.array_equal(values, np.round(values)) and (not values.size or np.abs(values).max() < EXACT_INTEGER):
        return [str(value) for value in values.astype(np.int64).tolist()]
    texts = (f"{value:.{precision}f}".rstrip("0").rstrip(".") for value in values.tolist())
    return [text if text != "-0" else "0" for text in texts]


def value_texts(column: np.ndarray, precision: int) -> list[str]:
    """Each item's value as escaped attribute text."""
    if column.dtype.kind in "fiub":
        return number_texts(column, precision)
    known: dict[object, str] = {}
    return [known[v] if v in known else known.setdefault(v, escape_attribute(format_value(v, precision)))
            for v in column.tolist()]


def matrix_texts(matrices: np.ndarray, precision: int) -> list[str]:
    """``translate(e f)`` per item when no item turns or scales, ``matrix(a b c d e f)`` otherwise."""
    parts = [number_texts(matrices[:, index], precision) for index in range(matrices.shape[1])]
    linear = matrices[:, :4]
    if np.array_equal(linear, np.broadcast_to([1.0, 0.0, 0.0, 1.0], linear.shape)):
        return [f"translate({e} {f})" for e, f in zip(parts[4], parts[5], strict=True)]
    return [f"matrix({a} {b} {c} {d} {e} {f})" for a, b, c, d, e, f in zip(*parts, strict=True)]


def point_texts(points: np.ndarray, offsets: np.ndarray, precision: int) -> list[str]:
    """Each item's ``points`` list (``x,y x,y ...``) from flat points split at *offsets*."""
    pairs = [f"{x},{y}" for x, y in zip(number_texts(points[:, 0], precision),
                                        number_texts(points[:, 1], precision), strict=True)]
    bounds = offsets.tolist()
    return [" ".join(pairs[start:stop]) for start, stop in zip(bounds[:-1], bounds[1:], strict=True)]
