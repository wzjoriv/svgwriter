"""
Tree rewrites that make a copy drawable by skia's SVG renderer.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ._layers import resolve_links

if TYPE_CHECKING:
    from ..elements.base import Element
    from ..elements.text import Text

__all__ = ["ellipses_as_paths", "expand_image_patterns", "outlined", "renderable_copy"]


def expand_image_patterns(root: Element) -> None:
    """Shapes filled with a pattern that holds images become clipped tiles, so the images get drawn."""
    from ..elements._geometry import PathOperand, replace_in_parent
    from ..elements.paint import Pattern

    for leaf in list(root.iter()):
        pattern = getattr(leaf.attributes.get("fill"), "element", None)
        if (isinstance(pattern, Pattern) and isinstance(leaf, PathOperand) and leaf.parent is not None
                and any(e.tag == "image" for e in pattern.iter())):
            try:
                replace_in_parent(leaf, leaf.expand_pattern())
            except (TypeError, ValueError):
                continue


def ellipses_as_paths(root: Element) -> None:
    """Replace ``<ellipse>`` by an equal ``<path>`` (skia's SVG renderer paints gradients on ellipses black)."""
    from ..elements.shapes import Ellipse, Path

    for ellipse in [e for e in root.iter() if isinstance(e, Ellipse)]:
        parent = ellipse.parent
        if parent is None:
            continue
        path = Path(ellipse.local_outline())
        path.attributes.update((k, v) for k, v in ellipse.attributes.items() if k not in ellipse.geometry_attributes)
        index = parent.children.index(ellipse)
        parent.remove(ellipse)
        parent.insert(index, path)


def outlined(text: Text) -> Element:
    """*text* as a ``<g>`` of per-run outline paths (keeps its transform, clip and opacity)."""
    from ..elements.structure import Group

    group = Group(*text.runs(), id=text.id, t=text.t)
    for name in ("clip-path", "mask", "filter", "opacity", "display", "visibility"):
        if text.has(name):
            group.attributes[name] = text.attributes[name]
    return group


def renderable_copy(root: Element, *, keep_text: Callable[[Text], bool] | None = None) -> Element:
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

    Returns
    -------
    Element
        A render-ready copy.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops._renderable import renderable_copy
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 5, 5)
    >>> renderable_copy(doc.root) is doc.root
    False
    """
    from ..attributes.cascade import resolve_styles
    from ..elements.text import Text

    copy = root.clone()
    resolve_styles(copy)
    resolve_links(copy)
    ellipses_as_paths(copy)
    expand_image_patterns(copy)
    if isinstance(copy, Text):
        return copy if keep_text is not None and keep_text(copy) else outlined(copy)
    for text in [e for e in copy.iter() if isinstance(e, Text)]:
        if keep_text is not None and keep_text(text):
            continue
        parent = text.parent
        assert parent is not None
        outline = outlined(text)
        index = parent.children.index(text)
        parent.remove(text)
        parent.insert(index, outline)
    return copy
