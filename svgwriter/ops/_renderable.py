"""
Tree rewrites that make a copy drawable by skia's SVG renderer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..elements.base import Element
    from ..elements.text import Text

__all__ = ["ellipses_as_paths", "expand_image_patterns", "outlined"]


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
