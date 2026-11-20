"""
The LaTeX groups that Office exports write as native equations, placed on the page.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..._internal._constants import LATEX_SIZE, LATEX_SOURCE

if TYPE_CHECKING:
    from ...document import Document

__all__ = ["Equation", "split_equations"]


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
    from ..._internal._rendering import page_box
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
