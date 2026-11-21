"""
Turning a batch's columns into real elements, one per item.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import numpy as np

from ..transform.matrix import Matrix
from ._kinds import INSTANCES, TEXTS

if TYPE_CHECKING:
    from ..elements.core import Element
    from ._batch import Batch

__all__ = ["build_items", "item_markup_names", "ordered_columns"]


def ordered_columns(batch: Batch) -> list[str]:
    """Column names in writing order: geometry first, then the rest as added."""
    columns = batch._columns or {}
    lead = [name for name in batch._kind.geometry if name in columns]
    return lead + [name for name in columns if name not in lead]


def item_markup_names(batch: Batch) -> list[str]:
    """Every attribute name written on each item."""
    names = (["xlink:href"] if batch._kind is INSTANCES else []) + ordered_columns(batch)
    if batch._points is not None:
        names.append("points")
    if batch._matrix is not None:
        names.append("transform")
    return names


def _blank(cls: type[Element], attributes: dict[str, Any], children: list[Any], parent: Element) -> Element:
    """An element of *cls* holding *attributes*, built without running each constructor."""
    element = cls.__new__(cls)
    element.__dict__.update(attributes=attributes, children=children, parent=parent)
    return element


def _rows(batch: Batch) -> Iterator[dict[str, Any]]:
    names = ordered_columns(batch)
    assert batch._columns is not None
    values = [batch._columns[name].tolist() for name in names]
    matrices = None if batch._matrix is None else [Matrix(*row) for row in batch._matrix.tolist()]
    for index, row in enumerate(zip(*values, strict=True) if values else ([()] * batch._count)):
        attributes = dict(zip(names, row, strict=True))
        if matrices is not None:
            attributes["transform"] = matrices[index]
        yield attributes


def build_items(batch: Batch) -> list[Element]:
    """One element per item of a compact *batch*, its children, carrying every column value.

    Text items keep ``(x, y)`` as their anchor and instances the shape's, so per-item rotation and
    scaling pivot where they did while the batch was compact.
    """
    kind = batch._kind
    cls = kind.element
    shared: dict[str, Any] = {}
    anchor: tuple[float, float] | None = None
    if kind is INSTANCES:
        shape = batch.shape
        assert shape is not None
        shared["xlink:href"] = shape.iri
        anchor = batch._shape_anchor()
    items: list[Element] = []
    content = batch._content.tolist() if batch._content is not None else None
    bounds = batch._offsets.tolist() if batch._offsets is not None else None
    for index, attributes in enumerate(_rows(batch)):
        item = _blank(cls, {**shared, **attributes}, [content[index]] if content is not None else [], batch)
        if bounds is not None:
            assert batch._points is not None
            item.set("points", np.array(batch._points[bounds[index]:bounds[index + 1]]))
        if kind is TEXTS:
            item.__dict__["_anchor"] = (float(attributes["x"]), float(attributes["y"]))
        elif anchor is not None:
            item.__dict__["_anchor"] = anchor
        items.append(item)
    return items
