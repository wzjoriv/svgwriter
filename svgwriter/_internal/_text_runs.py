"""
Text kept as text for vector exports: laid-out runs with their font, colour and page placement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ._constants import DEFAULT_SIZE, JOIN_TOLERANCE

if TYPE_CHECKING:
    from ..color.color import Color
    from ..document import Document
    from ..elements.core import Element
    from ..transform.matrix import Matrix

__all__ = ["TextRun", "text_runs"]


@dataclass
class TextRun:
    """One run of characters sharing an element, baseline and rotation.

    Attributes
    ----------
    text : str
        The characters.
    matrix : Matrix
        Maps the run's frame (origin at the start of the baseline, x along it, y down) to the page.
    size : float
        Font size in the run's frame.
    family : str
        CSS font family list.
    bold, italic : bool
        Weight and style.
    fill : Color or None
        Text color; None for unfilled text.
    opacity : float
        Fill opacity with group opacity included.
    width : float
        Advance width of the run.
    source : Element or None
        The ``<text>`` the run belongs to.
    """

    text: str
    matrix: Matrix
    size: float
    family: str
    bold: bool
    italic: bool
    fill: Color | None
    opacity: float
    width: float
    source: Element | None = field(default=None, compare=False, repr=False)


def _font(source: Element, rules: list[Any]) -> tuple[str, float, bool, bool]:
    from ..attributes.cascade import computed
    from ._fonts import font_size, font_weight

    family = str(computed(source, "font-family", "sans-serif", rules))
    size = font_size(computed(source, "font-size", DEFAULT_SIZE, rules))
    weight = font_weight(computed(source, "font-weight", "normal", rules))
    italic = str(computed(source, "font-style", "", rules)) in ("italic", "oblique")
    return family, size, weight >= 600, italic


def text_runs(document: Document, *, color_glyphs: bool = True) -> list[TextRun]:
    """Every ``<text>`` of *document* as page-placed runs, in paint order.

    Parameters
    ----------
    document : Document
        The document.
    color_glyphs : bool, optional
        Keep emoji in the runs; False leaves them out (splitting the run) for formats that place
        them as images. Defaults to True.

    Returns
    -------
    list of TextRun
        The runs; characters with their own rotation or position start a new run.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(100, 40)
    >>> _ = doc.text("Hello", x=10, y=30, font_size=20)
    >>> [(run.text, run.size, round(run.matrix.e, 1)) for run in text_runs(doc)]
    [('Hello', 20.0, 10.0)]
    """
    from ..attributes.cascade import rules_of
    from ..elements import Text
    from ..ops.render import page_size
    from ._flatten import _number
    from ._layers import ancestry
    from ._paints import _paint
    from ._rendering import view_matrix

    runs: list[TextRun] = []
    with document._prepared():
        width, height = page_size(document)
        view = view_matrix(document, width, height)
        root = document.root
        rules = rules_of(root)
        for text in [e for e in root.iter() if isinstance(e, Text)]:
            if str(text.get("display", "")) == "none":
                continue
            placement, opacity = ancestry(text, root)
            page = view @ placement
            current: list[Any] = []
            skip = 0
            for box in text.layout():
                if skip:
                    skip -= 1
                    continue
                if box.color is not None and not color_glyphs:
                    if current:
                        runs.append(_run(current, page, opacity, rules, _font, _paint, _number))
                    current, skip = [], len(box.color.text) - 1
                    continue
                if current and not _continues(current[-1], box):
                    runs.append(_run(current, page, opacity, rules, _font, _paint, _number))
                    current = []
                if box.char.strip() or current:
                    current.append(box)
            if current:
                runs.append(_run(current, page, opacity, rules, _font, _paint, _number))
    return [run for run in runs if run.text.strip()]


def _continues(previous: Any, box: Any) -> bool:
    return (box.source is previous.source and box.angle == previous.angle == 0
            and abs(box.y - previous.y) < JOIN_TOLERANCE
            and abs(box.x - (previous.x + previous.advance)) < JOIN_TOLERANCE)


def _run(boxes: list[Any], page: Matrix, opacity: float, rules: list[Any], font: Any, paint: Any, number: Any) -> TextRun:
    from ..transform.matrix import Matrix

    first, last = boxes[0], boxes[-1]
    family, size, bold, italic = font(first.source, rules)
    frame = page @ Matrix.translate(first.x, first.y) @ Matrix.rotate(first.angle)
    fill = paint(first.source, "fill", "black", rules)
    alpha = opacity * number(first.source, "fill-opacity", 1.0, rules) * number(first.source, "opacity", 1.0, rules)
    width = last.x + last.advance - first.x if first.angle == 0 else math.fsum(b.advance for b in boxes)
    return TextRun("".join(b.char for b in boxes).rstrip(), frame, size, family, bold, italic, fill, alpha, width,
                   _text_of(first.source))


def _text_of(element: Element) -> Element:
    """The ``<text>`` holding *element* (itself, or the ancestor of a ``tspan``)."""
    node: Element | None = element
    while node is not None and node.tag != "text":
        node = node.parent
    return node if node is not None else element
