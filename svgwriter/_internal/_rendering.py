"""
Tree rewrites that make a copy drawable by skia's SVG renderer, and the document ``viewBox`` mapping.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING

from ._conditions import apply_conditions
from ._constants import CONTAINERS, NONE, PRIMITIVE_PREFIX, VISIBILITY
from ._instances import expand_uses
from ._keywords import resolve_keywords
from ._layers import ancestry, drawable_order
from ._links import resolve_links
from ._markers import expand_markers
from ._servers import resolve_servers
from ._stops import linear_rgb_stops
from ._tiles import user_space_patterns
from ._tree import replace_in_parent
from ._viewports import flatten_viewports

if TYPE_CHECKING:
    from ..attributes.viewbox import ViewBox
    from ..document import Document
    from ..elements import Text
    from ..elements.core import Element
    from ..pathdata.data import BBox
    from ..transform.matrix import Matrix

__all__ = [
    "drop_foreign",
    "leaf_visibility",
    "expand_image_patterns",
    "outlined",
    "page_box",
    "renderable_copy",
    "shapes_as_paths",
    "unfiltered_masks",
    "view_matrix",
    "void_filters",
]


def expand_image_patterns(root: Element) -> None:
    """Shapes filled with a pattern skia cannot paint (holding images, or with a ``viewBox``) become clipped tiles."""
    from ..elements import PathOperand, Pattern
    from ._tree import resolve

    for leaf in list(root.iter()):
        pattern = resolve(leaf, leaf.attributes.get("fill")) if isinstance(leaf, PathOperand) else None
        if (isinstance(pattern, Pattern) and leaf.parent is not None
                and (pattern.get("viewBox") is not None or any(e.tag == "image" for e in pattern.iter()))):
            try:
                leaf.set("fill", pattern)
                replace_in_parent(leaf, leaf.expand_pattern())
            except (TypeError, ValueError):
                continue


def shapes_as_paths(root: Element) -> None:
    """Replace ``<ellipse>`` and ``<line>`` by equal ``<path>`` elements.

    Skia's SVG renderer paints gradients on both black. A line has no interior, so its path
    gets ``fill="none"`` (skia would paint the fill as a hairline).

    Parameters
    ----------
    root : Element
        A render copy; it is changed in place.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._rendering import shapes_as_paths
    >>> group = svg.group(svg.Line(0, 0, 5, 5, fill="red"))
    >>> shapes_as_paths(group)
    >>> group[0].tag, group[0].get("fill")
    ('path', 'none')
    """
    from ..elements.shapes import Ellipse, Line, Path

    for shape in [e for e in root.iter() if isinstance(e, (Ellipse, Line))]:
        parent = shape.parent
        if parent is None:
            continue
        path = Path(shape.local_outline())
        path.attributes.update((k, v) for k, v in shape.attributes.items() if k not in shape.geometry_attributes)
        if isinstance(shape, Line):
            path.attributes["fill"] = NONE
        index = parent.children.index(shape)
        parent.remove(shape)
        parent.insert(index, path)


def unfiltered_masks(root: Element) -> None:
    """Drop ``filter`` from every ``<mask>``: a mask is not rendered itself, so no filter applies to it."""
    for mask in [e for e in root.iter() if e.tag == "mask"]:
        mask.attributes.pop("filter", None)


def drop_foreign(root: Element) -> None:
    """Remove elements from other XML namespaces: they are not SVG, so nothing of them renders."""
    for element in [e for e in root.iter() if getattr(e, "namespace", None) is not None]:
        if element.parent is not None:
            element.parent.remove(element)


def void_filters(root: Element) -> None:
    """Hide elements whose ``filter`` names no ``<filter>`` or one without primitives: they render nothing."""
    from ._tree import resolve

    for element in list(root.iter()):
        value = element.attributes.get("filter")
        if value is None or str(value).strip() == NONE:
            continue
        target = resolve(element, value)
        if target is None or target.tag != "filter" or not any(
                not isinstance(child, str) and child.tag.startswith(PRIMITIVE_PREFIX) for child in target):
            element.attributes["display"] = NONE


def leaf_visibility(root: Element) -> None:
    """Move ``visibility`` from containers onto their children, which may override it (skia hides them all)."""
    for element in root.iter():
        if element.tag not in CONTAINERS or VISIBILITY not in element.attributes:
            continue
        value = element.attributes.pop(VISIBILITY)
        for child in element:
            if not isinstance(child, str):
                child.attributes.setdefault(VISIBILITY, value)


def outlined(text: Text) -> Element:
    """*text* as a ``<g>`` of per-run outline paths (keeps its transform, clip and opacity)."""
    from ..elements.structure import Group

    group = Group(*text.runs(), id=text.id, t=text.t)
    for name in ("clip-path", "mask", "filter", "opacity", "display", "visibility"):
        if text.has(name):
            group.attributes[name] = text.attributes[name]
    return group


def renderable_copy(root: Element, *, keep_text: Callable[[Text], bool] | None = None,
                    color_glyphs: bool = False) -> Element:
    """A copy of *root* with every ``<text>`` replaced by its glyph outlines.

    Skia's SVG renderer draws no text, so text is drawn as paths. Styles are resolved,
    local image links embedded and ellipses converted to paths on the copy.

    Parameters
    ----------
    root : Element
        The tree to copy; it is not modified.
    keep_text : callable, optional
        Texts it accepts stay ``<text>`` elements (to be drawn as real glyphs). Defaults to None,
        which outlines every text.
    color_glyphs : bool, optional
        Follow each outlined, rendered text that has colour glyphs (emoji, which have no outline)
        with a copy kept as ``<text>``, from which a canvas draws just those glyphs. Defaults to False.

    Returns
    -------
    Element
        A render-ready copy.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._rendering import renderable_copy
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 5, 5)
    >>> renderable_copy(doc.root) is doc.root
    False
    """
    from ..attributes.cascade import resolve_styles
    from ..elements import Text

    copy = root.clone()
    drop_foreign(copy)
    resolve_styles(copy)
    apply_conditions(copy)
    expand_uses(copy)
    resolve_keywords(copy)
    resolve_servers(copy)
    linear_rgb_stops(copy)
    flatten_viewports(copy)
    resolve_links(copy)
    shapes_as_paths(copy)
    unfiltered_masks(copy)
    leaf_visibility(copy)
    void_filters(copy)
    expand_image_patterns(copy)
    user_space_patterns(copy)
    expand_markers(copy)
    if isinstance(copy, Text):
        if keep_text is not None and keep_text(copy):
            return copy
        if color_glyphs and _has_color(copy):
            from ..elements.structure import Group

            return Group(outlined(copy), _color_layer(copy))
        return outlined(copy)
    rendered = {id(e) for e in drawable_order(copy)} if color_glyphs else set()
    for text in [e for e in copy.iter() if isinstance(e, Text)]:
        if keep_text is not None and keep_text(text):
            continue
        parent = text.parent
        assert parent is not None
        outline = outlined(text)
        index = parent.children.index(text)
        parent.remove(text)
        parent.insert(index, outline)
        if id(text) in rendered and _has_color(text):
            parent.insert(index + 1, _color_layer(text))
    return copy


def _has_color(text: Text) -> bool:
    return any(box.color is not None for box in text.layout())


def _color_layer(text: Text) -> Text:
    """*text* without its id, kept as ``<text>`` so its colour glyphs are drawn over its outlines."""
    layer = text.clone()
    layer.attributes.pop("id", None)
    return layer


def view_matrix(document: Document, width: float, height: float, box: ViewBox | None = None) -> Matrix:
    """The ``viewBox`` mapping of *document* onto a *width* by *height* page, centred and uniformly scaled."""
    from ..transform.matrix import IDENTITY, Matrix

    box = box or document.root.view_box
    if box is None or not box.width or not box.height:
        return IDENTITY
    s = min(width / box.width, height / box.height)
    return (Matrix.translate((width - box.width * s) / 2, (height - box.height * s) / 2)
            @ Matrix.scale(s) @ Matrix.translate(-box.min_x, -box.min_y))


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
    >>> from svgwriter._internal._rendering import page_box
    >>> doc = svg.Document(100, 100)
    >>> box = doc.add(svg.Group()).scale(2).add(svg.rect(1, 1, 4, 4))
    >>> page_box(doc, box)
    (BBox(x=2.0, y=2.0, width=8.0, height=8.0), 2.0)
    """
    from ..ops.render import document_size
    from ..pathdata.data import BBox

    with document._prepared():
        width, height = document_size(document)
        matrix = view_matrix(document, width, height) @ ancestry(element, document.root)[0]
    box = element.local_bbox()  # type: ignore[attr-defined]
    scale = math.sqrt(abs(matrix.determinant))
    if box is None:
        return None, scale
    corners = [(box.x, box.y), (box.x + box.width, box.y), (box.x, box.y + box.height),
               (box.x + box.width, box.y + box.height)]
    return BBox.from_points(matrix.apply(*corner) for corner in corners), scale
