"""
Interpolating two batches column by column: numbers, colours, point lists and per-item transforms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ._columns import frozen
from ._constants import COLOR_ATTRIBUTES, HALF, RGB
from ._paint import hex_column, rgba_of
from ._transforms import compose

if TYPE_CHECKING:
    from ._batch import Batch

__all__ = ["blend"]

HALF_TURN = np.pi


def _switch(a: Any, b: Any, t: float) -> Any:
    return a if t < HALF else b


def _colors(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    try:
        first, second = rgba_of(a), rgba_of(b)
    except ValueError:
        return _switch(a, b, t)
    return hex_column(first[:, :RGB] + (second[:, :RGB] - first[:, :RGB]) * t)[0]


def _column(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    if a.dtype.kind == "f" and b.dtype.kind == "f":
        return a + (b - a) * t
    if a.dtype == object and b.dtype == object:
        return _colors(a, b, t)
    return _switch(a, b, t)


def _decompose(m: np.ndarray) -> np.ndarray:
    """``(tx, ty, angle, skew, sx, sy)`` per item with ``M = translate rotate skewX scale`` (radians)."""
    a, b, c, d, e, f = m.T
    angle = np.arctan2(b, a)
    cos, sin = np.cos(angle), np.sin(angle)
    shear, sy = cos * c + sin * d, -sin * c + cos * d
    skew = np.arctan(np.divide(shear, sy, out=np.zeros_like(sy), where=sy != 0))
    return np.stack([e, f, angle, skew, np.hypot(a, b), sy], axis=1)


def _recompose(parts: np.ndarray) -> np.ndarray:
    tx, ty, angle, skew, sx, sy = parts.T
    cos, sin, tan = np.cos(angle), np.sin(angle), np.tan(skew)
    return np.stack([cos * sx, sin * sx, (cos * tan - sin) * sy, (sin * tan + cos) * sy, tx, ty], axis=1)


def _shift(points: np.ndarray, sign: float) -> np.ndarray:
    rows = np.zeros((len(points), 6))
    rows[:, 0] = rows[:, 3] = 1.0
    rows[:, 4:] = sign * points
    return rows


def _matrices(a: Batch, b: Batch, t: float) -> np.ndarray:
    """Translation, turn (the short way), skew and scale blended separately about the blended anchors."""
    pivot = a._anchors() + (b._anchors() - a._anchors()) * t
    inward, outward = _shift(pivot, -1.0), _shift(pivot, 1.0)
    first = _decompose(compose(compose(inward, a._matrices()), outward))
    second = _decompose(compose(compose(inward, b._matrices()), outward))
    delta = second - first
    delta[:, 2] = (delta[:, 2] + HALF_TURN) % (2 * HALF_TURN) - HALF_TURN
    return compose(compose(outward, _recompose(first + delta * t)), inward)


def _effective(batch: Batch, name: str) -> np.ndarray | None:
    """*batch*'s column *name*, or the value its ``<g>`` gives every item as a column."""
    assert batch._columns is not None
    if name in batch._columns:
        return batch._columns[name]
    value = batch.attributes.get(name)
    if value is None:
        return None
    if name in COLOR_ATTRIBUTES:
        try:
            return hex_column([value])[0].repeat(len(batch))
        except ValueError:
            return np.full(len(batch), value, dtype=object)
    return np.full(len(batch), value, dtype=float if isinstance(value, (int, float)) else object)


def _compatible(a: Batch, b: Batch) -> bool:
    from ..._internal._presets import INTERPOLATORS

    if a._kind is not b._kind or len(a) != len(b) or not (a.compact and b.compact):
        return False
    if a._offsets is not None and not np.array_equal(a._offsets, b._offsets):
        return False
    if INTERPOLATORS.attributes() & {*(a._columns or ()), *(b._columns or ())}:
        return False
    return a.shape is None or b.shape is None or a.shape.tag == b.shape.tag


def blend(a: Batch, b: Batch, t: float) -> Batch:
    """The batch a fraction *t* of the way from *a* to *b*, as :func:`svgwriter.interpolate` gives it.

    Compact batches of the same kind and size blend every column at once; other pairs of the same
    size, and batches with a column whose attribute has an interpolator of its own
    (``svg.preset.interpolator(attribute=...)``), blend item by item; batches of different sizes switch at ``t = 0.5``.
    """
    from ...ops.interpolate import interpolate

    if not _compatible(a, b):
        if len(a) != len(b):
            return _switch(a, b, t).clone()  # type: ignore[no-any-return]
        result = a.clone().expand()
        for item, other in zip(result.items, b.clone().expand().items, strict=True):
            mixed = interpolate(item, other, t)
            result.children[result.children.index(item)] = mixed
            mixed.parent = result
        return result
    result = a.clone()
    assert a._columns is not None and b._columns is not None and result._columns is not None
    for name in set(a._columns) | set(b._columns):
        first, second = _effective(a, name), _effective(b, name)
        result.attributes.pop(name, None)
        if first is None or second is None:
            chosen = _switch(first, second, t)
            if chosen is None:
                result._columns.pop(name, None)
            else:
                result._columns[name] = chosen
            continue
        result._columns[name] = frozen(np.asarray(_column(first, second, t)))
    if a._matrix is not None or b._matrix is not None:
        result._matrix = frozen(_matrices(a, b, t))
    if a._points is not None and b._points is not None:
        result._points = frozen(a._points + (b._points - a._points) * t)
    if a._content is not None and b._content is not None:
        result._content = _switch(a._content, b._content, t)
    return result
