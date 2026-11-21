"""
Writing a compact batch's items as markup, column by column.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._internal._escape import escape_attribute, escape_text
from ._expand import ordered_columns
from ._format import constant, matrix_texts, point_texts, value_texts
from ._kinds import INSTANCES

if TYPE_CHECKING:
    from ._batch import Batch

__all__ = ["item_markup"]


def _template_text(text: str) -> str:
    return text.replace("%", "%%")


def item_markup(batch: Batch, precision: int) -> list[str]:
    """Each item of a compact *batch* as one element of markup, in order.

    Columns holding one value for every item are formatted once and written into a shared
    template; the others are formatted as whole columns and filled in per item.
    """
    assert batch._columns is not None
    count = batch._count
    template = "<" + batch._kind.element.tag
    varying: list[list[str]] = []
    fields: list[tuple[str, list[str] | str]] = []
    for name in ordered_columns(batch):
        column = batch._columns[name]
        fields.append((name, value_texts(column[:1], precision)[0] if constant(column)
                       else value_texts(column, precision)))
    if batch._points is not None:
        assert batch._offsets is not None
        fields.append(("points", point_texts(batch._points, batch._offsets, precision)))
    if batch._kind is INSTANCES:
        shape = batch.shape
        assert shape is not None
        fields.insert(0, ("xlink:href", escape_attribute(shape.iri.svg_value(precision))))
    if batch._matrix is not None:
        fields.append(("transform", matrix_texts(batch._matrix, precision)))
    for name, texts in fields:
        if isinstance(texts, str):
            template += f' {name}="{_template_text(texts)}"'
        else:
            template += f' {name}="%s"'
            varying.append(texts)
    if batch._content is not None:
        template += ">%s</" + batch._kind.element.tag + ">"
        varying.append([escape_text(text) for text in batch._content.tolist()])
    else:
        template += "/>"
    if not varying:
        return [template.replace("%%", "%")] * count
    return [template % row for row in zip(*varying, strict=True)]
