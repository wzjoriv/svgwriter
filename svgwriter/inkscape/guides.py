"""
Inkscape guides: ``<sodipodi:guide>`` lines inside ``<sodipodi:namedview>``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .._internal._constants import SODIPODI_NS
from .._internal._numbers import format_number
from ..elements.core import Element, UnknownElement
from ._constants import (
    FALSE,
    GUIDE_COLOR,
    GUIDE_LOCKED,
    GUIDE_ORIENTATION,
    GUIDE_POSITION,
    GUIDE_PRECISION,
    GUIDE_TAG,
    HALF_TURN_DEGREES,
    HORIZONTAL,
    LABEL,
    NAMEDVIEW_TAG,
    TRUE,
    VERTICAL,
)

__all__ = ["Guide", "guides", "namedview", "set_guides"]

@dataclass(frozen=True)
class Guide:
    """A guide line, in the document's user units with y pointing down.

    Parameters
    ----------
    x, y : float
        A point the line passes through.
    angle : float, optional
        Direction of the line in degrees, clockwise from the x axis: 0 is
        horizontal, 90 vertical. Defaults to 0.
    label : str, optional
        The name shown next to the guide. Defaults to None.
    color : str, optional
        Guide colour, as Inkscape writes it (``"#0000ff"``). Defaults to None.
    locked : bool, optional
        Whether the guide can be dragged. Defaults to False.

    See Also
    --------
    svgwriter.Document.guides : Read or replace a document's guides.

    Notes
    -----
    Inkscape stores guide positions from the bottom-left of the ``viewBox`` with y
    pointing up, and the orientation as the line's normal; reading and writing
    convert both, so guides line up with the drawing's own coordinates.

    Examples
    --------
    >>> from svgwriter.inkscape import Guide
    >>> Guide.vertical(10).angle, Guide.horizontal(5, label="base").y
    (90.0, 5)
    """

    x: float
    y: float
    angle: float = HORIZONTAL
    label: str | None = None
    color: str | None = None
    locked: bool = False

    @classmethod
    def horizontal(cls, y: float, **kwargs: object) -> Guide:
        """A horizontal guide at height *y*.

        Examples
        --------
        >>> from svgwriter.inkscape import Guide
        >>> Guide.horizontal(20)
        Guide(x=0.0, y=20, angle=0.0, label=None, color=None, locked=False)
        """
        return cls(0.0, y, HORIZONTAL, **kwargs)  # type: ignore[arg-type]

    @classmethod
    def vertical(cls, x: float, **kwargs: object) -> Guide:
        """A vertical guide at *x*.

        Examples
        --------
        >>> from svgwriter.inkscape import Guide
        >>> Guide.vertical(20).x
        20
        """
        return cls(x, 0.0, VERTICAL, **kwargs)  # type: ignore[arg-type]


def _frame(root: Element) -> tuple[float, float, float]:
    """The viewBox x, y and height that Inkscape measures guides against."""
    box = root.attributes.get("viewBox")
    if box is not None:
        values = [float(v) for v in str(box.svg_value() if hasattr(box, "svg_value") else box).replace(",", " ").split()]
        return values[0], values[1], values[3]
    height = root.attributes.get("height")
    number = getattr(height, "value", height)
    return 0.0, 0.0, float(number) if number is not None else 0.0


def namedview(root: Element, *, create: bool = False) -> Element | None:
    """The ``<sodipodi:namedview>`` holding Inkscape's view settings and guides.

    Parameters
    ----------
    root : Element
        A document's ``<svg>``.
    create : bool, optional
        Add an empty one when there is none. Defaults to False.

    Returns
    -------
    Element or None
        The element, or None when there is none and `create` is False.

    Examples
    --------
    >>> import svgwriter as svg
    >>> root = svg.svg()
    >>> svg.inkscape.namedview(root) is None, svg.inkscape.namedview(root, create=True).tag
    (True, 'namedview')
    """
    for child in root.children:
        if isinstance(child, UnknownElement) and child.tag == NAMEDVIEW_TAG and child.namespace == SODIPODI_NS:
            return child
    if not create:
        return None
    view = UnknownElement(NAMEDVIEW_TAG, namespace=SODIPODI_NS)
    view.parent = root
    root.children.insert(0, view)
    return view


def guides(root: Element) -> list[Guide]:
    """The guides of an Inkscape document.

    Parameters
    ----------
    root : Element
        A document's ``<svg>``.

    Returns
    -------
    list of Guide
        In file order, in user units with y pointing down.

    Examples
    --------
    >>> import svgwriter as svg
    >>> root = svg.svg(view_box="0 0 100 50")
    >>> svg.inkscape.set_guides(root, [svg.inkscape.Guide.horizontal(10)])
    >>> svg.inkscape.guides(root)[0].y
    10.0
    """
    view = namedview(root)
    if view is None:
        return []
    left, top, height = _frame(root)
    found = []
    for child in view.children:
        if not isinstance(child, Element) or child.tag != GUIDE_TAG:
            continue
        attributes = child.attributes
        x, y = (float(v) for v in str(attributes.get(GUIDE_POSITION, "0,0")).split(","))
        nx, ny = (float(v) for v in str(attributes.get(GUIDE_ORIENTATION, "0,1")).split(","))
        angle = math.degrees(math.atan2(nx, ny)) % HALF_TURN_DEGREES
        color = attributes.get(GUIDE_COLOR)
        found.append(Guide(x + left, top + height - y, angle, child.label, None if color is None else str(color),
                           str(attributes.get(GUIDE_LOCKED, FALSE)).lower() == TRUE))
    return found


def set_guides(root: Element, lines: list[Guide]) -> None:
    """Replace the guides of a document.

    Parameters
    ----------
    root : Element
        A document's ``<svg>``; a ``<sodipodi:namedview>`` is added if needed.
    lines : list of Guide
        The new guides.

    Examples
    --------
    >>> import svgwriter as svg
    >>> root = svg.svg(view_box="0 0 100 50")
    >>> svg.inkscape.set_guides(root, [svg.inkscape.Guide.vertical(30)])
    >>> svg.inkscape.namedview(root).children[0].attributes["position"]
    '30,50'
    """
    view = namedview(root, create=True)
    assert view is not None
    view.children = [child for child in view.children if not (isinstance(child, Element) and child.tag == GUIDE_TAG)]
    left, top, height = _frame(root)
    for line in lines:
        radians = math.radians(line.angle)
        guide = UnknownElement(GUIDE_TAG, namespace=SODIPODI_NS)
        guide.attributes.update({
            GUIDE_POSITION: f"{_text(line.x - left)},{_text(top + height - line.y)}",
            GUIDE_ORIENTATION: f"{_text(math.sin(radians))},{_text(math.cos(radians))}",
            GUIDE_LOCKED: TRUE if line.locked else FALSE,
        })
        if line.label is not None:
            guide.attributes[LABEL] = line.label
        if line.color is not None:
            guide.attributes[GUIDE_COLOR] = line.color
        guide.parent = view
        view.children.append(guide)


def _text(value: float) -> str:
    return format_number(value, GUIDE_PRECISION)
