"""
Pattern fills cut into plain tiles, and images placed in page space, for flattening.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..document import Document
    from ..elements.core import Element
    from ..pathdata.data import PathData
    from ..transform.matrix import Matrix

__all__ = ["placed_images"]


def _ancestry(leaf: Element, root: Element) -> tuple[Matrix, float]:
    from ..elements import Transformable
    from ..transform.matrix import IDENTITY

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
    from ..elements import Group, PathOperand, Pattern
    from ._layers import drawable_order
    from ._tree import replace_in_parent

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
    from ..elements import PathOperand
    from ..ops.boolean import intersection
    from ..transform.matrix import Matrix

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


def placed_images(document: Document) -> list[tuple[Any, Matrix]]:
    """Each embedded image with the matrix from its pixel grid to page coordinates (``viewBox`` included).

    Formats that draw images themselves (EPS, PowerPoint) use this; :func:`flatten` leaves images out.

    Parameters
    ----------
    document : Document
        The document.

    Returns
    -------
    list of (Image, Matrix)
        Images in paint order with their placement.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> doc = svg.Document(20, 10)
    >>> _ = doc.add(svg.Image(np.zeros((2, 4, 3)), 5, 0, 8, 4))
    >>> [matrix.apply(0, 0) for _, matrix in placed_images(doc)]
    [Point(x=5.0, y=0.0)]
    """
    from ..elements import Image
    from ..ops.render import document_size
    from ._layers import ancestry, image_matrix
    from ._rendering import view_matrix

    with document._sized():
        width, height = document_size(document)
        view = view_matrix(document, width, height)
        images = [element for element in document.root.iter() if isinstance(element, Image)]
        return [(image, view @ ancestry(image, document.root)[0] @ image_matrix(image))
                for image in images if image.pixels is not None]
