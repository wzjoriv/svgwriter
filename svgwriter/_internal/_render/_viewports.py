"""
Nested ``<svg>`` viewports rewritten as placed, clipped groups, which skia's SVG renderer draws faithfully.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._constants import NESTED_VIEWPORT_ID, PERCENT, USE_GEOMETRY, VISIBLE_OVERFLOW

if TYPE_CHECKING:
    from ...elements.core import Element

__all__ = ["flatten_viewports"]


def _length(element: Element, name: str, extent: float, default: str) -> float:
    from ...attributes.length import Length, Unit

    length = Length.parse(element.get(name, default))
    return length.value * extent / PERCENT if length.unit is Unit.PERCENT else float(length.to_user_units())


def _matrix_text(element: Element, width: float, height: float) -> str | None:
    """The ``viewBox`` mapping of *element* into its *width* by *height* viewport, as transform text."""
    from ...attributes.viewbox import PreserveAspectRatio, ViewBox
    from ...transform.matrix import Matrix
    from ._layers import fit_box

    box = element.get("viewBox")
    box = box if isinstance(box, ViewBox) or box is None else ViewBox.parse(str(box))
    if box is None or not box.width or not box.height:
        return None
    ratio = element.get("preserveAspectRatio")
    ratio = ratio if isinstance(ratio, PreserveAspectRatio) else (
        PreserveAspectRatio.parse(str(ratio)) if ratio is not None else PreserveAspectRatio())
    m = fit_box(width, height, box.width, box.height, ratio) @ Matrix.translate(-box.min_x, -box.min_y)
    return f"matrix({m.a} {m.b} {m.c} {m.d} {m.e} {m.f})"


def flatten_viewports(root: Element) -> None:
    """Replace every nested ``<svg>`` under *root* by groups that place, fit and clip its content.

    The content keeps its identity (ids stay valid): it moves into a group carrying the
    ``viewBox`` mapping, inside a group translated to ``x``/``y`` and clipped to the viewport
    unless ``overflow`` shows it.

    Parameters
    ----------
    root : Element
        A render copy; it is changed in place.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._viewports import flatten_viewports
    >>> doc = svg.Document.from_string('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
    ...                                '<svg x="2" width="5" height="5"><rect width="9" height="9"/></svg></svg>')
    >>> flatten_viewports(doc.root)
    >>> [e.tag for e in doc.root.iter()]
    ['svg', 'clipPath', 'rect', 'g', 'g', 'rect']
    """
    from ...elements import ClipPath, Group, Rect
    from .._tree import replace_in_parent
    from ._layers import viewport_extent

    nested_viewports = [e for e in root.iter() if e.tag == "svg" and e is not root]
    for serial, nested in enumerate(reversed(nested_viewports), start=1):
        if nested.parent is None:
            continue
        extent = viewport_extent(nested)
        width = _length(nested, "width", extent[0], "100%")
        height = _length(nested, "height", extent[1], "100%")
        children = list(nested.children)
        for child in children:
            if not isinstance(child, str):
                nested.remove(child)
        content = Group(*[child for child in children if not isinstance(child, str)])
        content.attributes.update((k, v) for k, v in nested.attributes.items()
                                  if k not in USE_GEOMETRY and k not in ("viewBox", "preserveAspectRatio", "overflow",
                                                                        "version", "baseProfile"))
        mapping = _matrix_text(nested, width, height)
        if mapping is not None:
            content.attributes["transform"] = mapping
        holder = Group(content)
        if nested.get("id") is not None:
            holder.attributes["id"] = nested.get("id")
        holder.attributes["transform"] = (f"translate({_length(nested, 'x', extent[0], '0')} "
                                          f"{_length(nested, 'y', extent[1], '0')})")
        parts: list[Element] = [holder]
        if str(nested.get("overflow", "hidden")) not in VISIBLE_OVERFLOW and width and height:
            clip = ClipPath(Rect(0, 0, width, height), id=f"{NESTED_VIEWPORT_ID}{serial}")
            holder.attributes["clip-path"] = f"url(#{clip.id})"
            parts.insert(0, clip)
        parent = nested.parent
        index = parent.children.index(nested)
        replace_in_parent(nested, parts[-1])
        if len(parts) > 1:
            parent.insert(index, parts[0])
