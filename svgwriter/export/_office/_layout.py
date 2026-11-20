"""
Page placement for Office exports: element boxes on the page and the LaTeX groups written as native equations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..._internal._constants import LATEX_SIZE, LATEX_SOURCE

if TYPE_CHECKING:
    from ...document import Document
    from ...elements.core import Element
    from ...pathdata.data import BBox

__all__ = ["Equation", "page_box", "split_equations"]


@dataclass(frozen=True)
class Equation:
    """A LaTeX group to write as an Office equation, placed on the page.

    Attributes
    ----------
    source : str
        The LaTeX math, known to convert to Office math.
    x, y, width, height : float
        The group's box on the page, in user units.
    size : float
        Font size on the page, in user units.

    Examples
    --------
    >>> from svgwriter.export._office._layout import Equation
    >>> Equation("x", 0, 0, 10, 10, 12).size
    12
    """

    source: str
    x: float
    y: float
    width: float
    height: float
    size: float


def page_box(document: Document, element: Element) -> tuple[BBox | None, float]:
    """The box of *element* on the page (ancestor transforms and ``viewBox`` applied) and its linear scale.

    Parameters
    ----------
    document : Document
        The document holding *element*.
    element : Element
        A sized element.

    Returns
    -------
    tuple of (BBox or None, float)
        The page box (None when the element has no size) and the square root
        of the page transform's determinant.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._office._layout import page_box
    >>> doc = svg.Document(100, 100)
    >>> box = doc.add(svg.Group()).scale(2).add(svg.rect(1, 1, 4, 4))
    >>> page_box(doc, box)
    (BBox(x=2.0, y=2.0, width=8.0, height=8.0), 2.0)
    """
    from ..._internal._layers import ancestry
    from ..._internal._rendering import view_matrix
    from ...ops.render import document_size
    from ...pathdata.data import BBox

    with document._sized():
        width, height = document_size(document)
        matrix = view_matrix(document, width, height) @ ancestry(element, document.root)[0]
    box = element.local_bbox()  # type: ignore[attr-defined]
    scale = math.sqrt(abs(matrix.determinant))
    if box is None:
        return None, scale
    corners = [(box.x, box.y), (box.x + box.width, box.y), (box.x, box.y + box.height),
               (box.x + box.width, box.y + box.height)]
    return BBox.from_points(matrix.apply(*corner) for corner in corners), scale


def split_equations(document: Document) -> tuple[Document, list[Equation]]:
    """A copy of *document* without the LaTeX groups that convert to Office math, and those equations.

    Groups made by :func:`svgwriter.latex` carry their source; each one whose
    source converts is taken out of the copy and returned as an
    :class:`Equation`. Groups that do not convert stay in the copy as outlines.

    Parameters
    ----------
    document : Document
        The drawing; it is not changed.

    Returns
    -------
    tuple of (Document, list of Equation)
        The remaining drawing and the equations in document order.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._office._layout import split_equations
    >>> doc = svg.Document(100, 40)
    >>> _ = doc.add(svg.latex("x^2", engine="mathtext")).place(20, 20)
    >>> rest, found = split_equations(doc)
    >>> len(rest), [e.source for e in found]
    (0, ['x^2'])
    """
    from ...document import Document
    from ._omml import latex_to_omml

    copy = Document(root=document.root.clone())
    equations: list[Equation] = []
    for group in [element for element in copy.root.iter() if element.get(LATEX_SOURCE) is not None]:
        if any(ancestor.get(LATEX_SOURCE) is not None for ancestor in _ancestors(group)):
            continue
        source = str(group.get(LATEX_SOURCE))
        box, scale = page_box(copy, group)
        try:
            latex_to_omml(source)
        except (ValueError, ImportError):
            continue
        if box is None or group.parent is None:
            continue
        equations.append(Equation(source, box.x, box.y, box.width, box.height,
                                  float(group.get(LATEX_SIZE) or 0) * scale))
        group.parent.remove(group)
    return copy, equations


def _ancestors(element: Any) -> list[Any]:
    chain, node = [], element.parent
    while node is not None:
        chain.append(node)
        node = node.parent
    return chain
