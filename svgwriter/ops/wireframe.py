"""
Wireframes for debugging: a copy of a drawing where every shape, text and image is a thin outline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._constants import (
    WIREFRAME_BOUNDS_DASH,
    WIREFRAME_COLOR,
    WIREFRAME_DROPPED,
    WIREFRAME_WIDTH,
    WIREFRAME_WIDTH_SHARE,
)

if TYPE_CHECKING:
    from ..document import Document
    from ..model.elements.core import Element

__all__ = ["wireframe"]


def wireframe(target: Document | Element, *, color: str = WIREFRAME_COLOR, width: float | None = None,
              bounds: bool = False) -> Any:
    """A copy of *target* drawn as thin outlines, to see the geometry under the paint.

    Shapes and text keep their geometry and type sizes with no fill and a *width* stroke in *color* (set in
    their inline style, so theme roles cannot repaint them); images become their box. Filters, masks, opacity, markers and animations are left out, and the original is not changed.

    Parameters
    ----------
    target : Document or Element
        The drawing.
    color : str, optional
        Outline colour. Defaults to sky blue.
    width : float, optional
        Outline width in user units. Defaults to None: 1/600 of the drawing's larger side, a hairline at any
        page size.
    bounds : bool, optional
        Also draw each shape's bounding box, dashed. Defaults to False.

    Returns
    -------
    Document or Element
        The wireframe, of the same kind as *target*.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(width=80, height=40)
    >>> _ = doc.rect(5, 5, 30, 30, fill="crimson", filter=svg.filters.drop_shadow())
    >>> _ = doc.text("Hi", x=45, y=28, font_size=20)
    >>> wire = doc.wireframe()
    >>> rect = wire.root.find("rect")
    >>> rect.style["fill"], rect.style["stroke"], rect.get("filter")
    ('none', '#0ea5e9', None)
    >>> doc.root.find("rect").get("fill")
    'crimson'
    """
    from ..document import Document
    from ..model.elements.animation import AnimationElement
    from ..model.elements.shapes import Rect
    from ..model.elements.structure import Image

    copy = Document(root=target.root.clone(), theme=target.theme) if isinstance(target, Document) else target.clone()
    root = copy.root if isinstance(copy, Document) else copy
    if width is None:
        view = root.get("viewBox") if root.tag == "svg" else None
        box = view if hasattr(view, "width") else (root.local_bbox() if hasattr(root, "local_bbox") else None)
        sides = [float(box.width), float(box.height)] if box is not None else []
        width = max(sides) / WIREFRAME_WIDTH_SHARE if sides and max(sides) > 0 else WIREFRAME_WIDTH
    for element in list(root.iter()):
        if isinstance(element, AnimationElement):
            if element.parent is not None:
                element.parent.remove(element)
            continue
        for name in WIREFRAME_DROPPED:
            element.attributes.pop(name, None)
        if "style" in element.attributes:
            style = element.style
            for name in WIREFRAME_DROPPED:
                style.pop(name, None)
            element.style = style
        if isinstance(element, Image):
            box = Rect(element.get("x") or 0, element.get("y") or 0, element.get("width") or 0,
                       element.get("height") or 0, transform=element.get("transform"))
            parent = element.parent
            if parent is not None:
                parent.insert(parent.children.index(element), box)
                parent.remove(element)
            element = box
        if element.tag in _PAINTED:
            style = element.style
            style.update({"fill": "none", "stroke": color, "stroke-width": f"{width:g}px"})
            element.style = style
            parent = element.parent
            if bounds and element.tag != "text" and parent is not None and parent.tag not in _DEFINITIONS:
                found = element.bounds() if hasattr(element, "bounds") else None
                if found is not None:
                    box = Rect(found.x, found.y, found.width, found.height, fill="none", stroke=color,
                               stroke_width=width / 2, stroke_dasharray=WIREFRAME_BOUNDS_DASH)
                    parent.insert(parent.children.index(element) + 1, box)
    return copy


_PAINTED = frozenset({"rect", "circle", "ellipse", "line", "polyline", "polygon", "path", "text", "tspan",
                      "textPath", "use"})
"""Tags whose paint the wireframe replaces with an outline."""
_DEFINITIONS = frozenset({"defs", "pattern", "clipPath", "mask", "marker", "symbol", "linearGradient",
                          "radialGradient", "filter"})
"""Containers whose children are not drawn in place, so they get no bounding box."""
