"""
``textLength`` and ``lengthAdjust``: stretching or squeezing laid-out text to an author-given advance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...transform.matrix import Matrix
from ._constants import SPACING_AND_GLYPHS

if TYPE_CHECKING:
    from ..core import Element
    from ._textlayout import Char

__all__ = ["fit_lengths"]


def fit_lengths(chars: list[Char], boxes: list[Any], chunks: list[int], width: float) -> None:
    """Meet every ``textLength`` in *chars*, outermost element first, shifting the rest of each chunk along.

    Parameters
    ----------
    chars : list of Char
        The rendered characters, as collected.
    boxes : list of GlyphBox
        Their glyph boxes, adjusted in place.
    chunks : list of int
        Indices where text chunks start (an absolute ``x``), ending with ``len(boxes)``.
    width : float
        Viewport width that percentage lengths resolve against.

    Examples
    --------
    >>> import svgwriter as svg
    >>> boxes = svg.text("ab", x=0, y=10, text_length=100).layout()
    >>> round(boxes[-1].x + boxes[-1].advance, 6)
    100.0
    """
    from ._textlayout import number_list

    holders: dict[int, tuple[Element, list[int]]] = {}
    for index, char in enumerate(chars):
        for element in char.chain:
            if element.get("textLength") is not None:
                holders.setdefault(id(element), (element, []))[1].append(index)
    for element, indices in sorted(holders.values(), key=lambda item: -len(item[1])):
        target = number_list(element.get("textLength"), width)
        first, last = indices[0], indices[-1]
        extent = boxes[last].x + boxes[last].advance - boxes[first].x
        if not target or target[0] < 0 or extent <= 0:
            continue
        end = next((c for c in chunks if c > last), len(boxes))
        if str(element.get("lengthAdjust", "")) == SPACING_AND_GLYPHS:
            _scale(boxes, first, last, end, target[0] / extent)
        else:
            _space(boxes, first, last, end, target[0] - extent)


def _scale(boxes: list[Any], first: int, last: int, end: int, factor: float) -> None:
    origin = boxes[first].x
    stretch = Matrix.scale(factor, 1.0)
    for box in boxes[first:last + 1]:
        box.x = origin + (box.x - origin) * factor
        box.advance *= factor
        box.outline = box.outline.transformed(stretch)
    shift = (boxes[last].x + boxes[last].advance) - (origin + (boxes[last].x - origin) / factor
                                                      + boxes[last].advance / factor)
    for box in boxes[last + 1:end]:
        box.x += shift


def _space(boxes: list[Any], first: int, last: int, end: int, extra: float) -> None:
    gaps = max(last - first, 1)
    for step, box in enumerate(boxes[first:last + 1]):
        box.x += extra * step / gaps
    if last == first:
        boxes[first].advance += extra
    for box in boxes[last + 1:end]:
        box.x += extra
