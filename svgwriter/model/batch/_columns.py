"""
Broadcasting arguments into item columns: geometry, per-item attributes and the batch's own attributes.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..attributes.cascade import INHERITED
from ..attributes.names import PRESENTATION_ATTRIBUTES, svg_name
from ..elements.core import Element
from ._constants import COLOR_ATTRIBUTES, LIST_VALUED, OPACITY_FOR
from ._paint import hex_column, is_color_column

__all__ = ["Columns", "broadcast", "frozen"]


@dataclass
class Columns:
    """Arguments sorted into one value per item and attributes of the batch itself."""

    count: int
    shape: tuple[int, ...]
    items: dict[str, np.ndarray] = field(default_factory=dict)
    shared: dict[str, Any] = field(default_factory=dict)


def frozen(array: np.ndarray) -> np.ndarray:
    """*array* made read-only, so columns can be shared between copies of a batch."""
    if array.flags.writeable:
        array.flags.writeable = False
    return array


def _per_item(name: str, value: Any) -> bool:
    if name in COLOR_ATTRIBUTES:
        return is_color_column(value)
    if isinstance(value, np.ndarray):
        return value.ndim >= 1
    return isinstance(value, (list, tuple)) and name not in LIST_VALUED


def _item_array(name: str, value: Any) -> tuple[np.ndarray, np.ndarray | None]:
    if name in COLOR_ATTRIBUTES:
        return hex_column(value)
    array = np.asarray(value)
    if array.dtype.kind in "iu":
        return array.astype(float), None
    if array.dtype.kind not in "fb":
        array = np.asarray(value, dtype=object)
    return array, None


def _shared_on_batch(name: str, value: Any) -> bool:
    """Inherited properties, non-presentation attributes and references sit once on the ``<g>``."""
    return name in INHERITED or name not in PRESENTATION_ATTRIBUTES or isinstance(value, Element)


def broadcast(geometry: Mapping[str, Any], attributes: Mapping[str, Any], *,
              count: int | None = None, shapes: tuple[tuple[int, ...], ...] = ()) -> Columns:
    """Broadcast *geometry* and per-item *attributes* to one value per item (numpy rules).

    Parameters
    ----------
    geometry : mapping
        Numeric arguments by SVG name; every one becomes a column.
    attributes : mapping
        Attributes by Python or SVG name: arrays, colour lists and ``(..., 3|4)`` colour arrays
        become columns; other values are shared.
    count : int, optional
        The batch's item count, which the result must keep. Defaults to None.
    shapes : tuple of tuple of int, optional
        Further item shapes taking part in the broadcast. Defaults to none.

    Returns
    -------
    Columns
        Flat read-only columns of ``count`` items, and the shared attributes.

    Raises
    ------
    ValueError
        If the shapes do not broadcast, or do not give *count* items.
    """
    arrays: dict[str, np.ndarray] = {name: np.asarray(value, dtype=float) for name, value in geometry.items()}
    scalars: dict[str, Any] = {}
    for key, value in attributes.items():
        name = svg_name(key)
        if value is None:
            continue
        if not _per_item(name, value):
            scalars[name] = value
            continue
        array, alpha = _item_array(name, value)
        arrays[name] = array
        if alpha is not None and OPACITY_FOR.get(name) not in arrays:
            arrays[OPACITY_FOR[name]] = alpha
    try:
        shape = np.broadcast_shapes(*(array.shape for array in arrays.values()), *shapes,
                                    *(((count,),) if count is not None else ()))
    except ValueError as error:
        sizes = ", ".join(f"{name} {array.shape}" for name, array in arrays.items())
        expected = "" if count is None else f" and one value per item ({count})"
        raise ValueError(f"batch arguments do not broadcast together{expected}: {sizes}") from error
    total = math.prod(shape)
    if count is not None and total != count:
        raise ValueError(f"expected one value per item ({count}), got shape {shape}")
    columns = Columns(total, shape)
    for name, array in arrays.items():
        columns.items[name] = frozen(np.broadcast_to(array, shape).reshape(total))
    for name, value in scalars.items():
        if _shared_on_batch(name, value):
            columns.shared[name] = value
        else:
            columns.items[name] = frozen(np.broadcast_to(np.asarray(value, dtype=_dtype(value)), (total,)))
    return columns


def _dtype(value: Any) -> Any:
    return float if isinstance(value, (int, float, np.number)) and not isinstance(value, bool) else object
