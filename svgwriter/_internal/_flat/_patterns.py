"""
Pattern fills cut into plain tiles for flattening.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...model.elements.core import Element
    from ...model.pathdata.data import PathData
    from ...model.transform.matrix import Matrix

__all__: list[str] = []


def _ancestry(leaf: Element, root: Element) -> tuple[Matrix, float]:
    from ...model.elements import Transformable
    from ...model.transform.matrix import IDENTITY

    matrix, opacity = IDENTITY, 1.0
    node = leaf.parent
    while node is not None and node is not root:
        if isinstance(node, Transformable):
            matrix = node.t @ matrix
        opacity *= float(node.get("opacity", 1.0))
        node = node.parent
    return matrix, opacity


def _expand_patterns(root: Element) -> None:
    """Replace pattern-filled shapes by their tiles cut to the outline, so vector formats keep patterns."""
    from ...model.elements import Group, PathOperand, Pattern
    from .._render._layers import drawable_order
    from .._tree import replace_in_parent

    for leaf in drawable_order(root):
        pattern = getattr(leaf.attributes.get("fill"), "element", None)
        if not isinstance(pattern, Pattern) or not isinstance(leaf, PathOperand):
            continue
        box = leaf.local_bbox()
        if box is None:
            continue
        try:
            tiles = _cut_tiles(pattern, box, leaf.local_outline())
        except ValueError:
            continue
        holder = Group(*tiles)
        holder.t = leaf.t
        if leaf.get("stroke") not in (None, "none"):
            outline = leaf.clone()
            outline.set("fill", "none")
            outline.discard("transform")
            holder.add(outline)
        replace_in_parent(leaf, holder)


def _cut_tiles(pattern: Any, box: Any, outline: PathData) -> list[Any]:
    """Each shape of each tile as a ``<path>`` intersected with *outline* (pattern transform baked in)."""
    from ...model.elements import PathOperand
    from ...model.transform.matrix import Matrix
    from ...ops.boolean import intersection

    tile = pattern.tile(box)
    inverse = pattern.t.inverse()
    corners = [inverse.apply(x, y) for x in (box.x, box.x + box.width) for y in (box.y, box.y + box.height)]
    xs, ys = [c.x for c in corners], [c.y for c in corners]
    paths = []
    for row in range(math.floor((min(ys) - tile.y) / tile.height), math.ceil((max(ys) - tile.y) / tile.height)):
        for column in range(math.floor((min(xs) - tile.x) / tile.width),
                            math.ceil((max(xs) - tile.x) / tile.width)):
            offset = pattern.t @ Matrix.translate(tile.x + column * tile.width, tile.y + row * tile.height)
            for shape in pattern.iter():
                if shape is pattern or not isinstance(shape, PathOperand) or len(shape):
                    continue
                piece = shape.to_path().transformed(offset)
                clipped = intersection(piece.d, outline)
                if len(clipped):
                    piece.d = clipped
                    paths.append(piece)
    return paths

