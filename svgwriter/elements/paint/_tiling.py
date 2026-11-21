"""
Tiling and rasterising ``<pattern>`` paint servers.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from ...pathdata.data import BBox
from .._behavior import positioned_bbox

if TYPE_CHECKING:
    from ..structure import Group, Image
    from ._pattern import Pattern


__all__ = ["PatternTiling"]


class PatternTiling:
    """Tile documents, rasters and patterns made from images; mixed into :class:`~svgwriter.elements.Pattern`."""

    __slots__ = ()

    def tile(self, target: BBox | None = None) -> BBox:
        """The tile rectangle in user units, resolving ``objectBoundingBox`` sizes against *target*.

        Parameters
        ----------
        target : BBox, optional
            Box of the element being painted; needed when ``patternUnits`` is
            ``objectBoundingBox`` (the SVG default). Defaults to None.

        Returns
        -------
        BBox
            Position and size of one tile before ``patternTransform``.

        Raises
        ------
        ValueError
            If the size is relative and no *target* is given, or the tile is empty.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Pattern(width=0.5, height=0.25).tile(svg.BBox(0, 0, 40, 40))
        BBox(x=0.0, y=0.0, width=20.0, height=10.0)
        """
        box = positioned_bbox(self) or BBox(0.0, 0.0, 0.0, 0.0)
        if str(self.get("patternUnits", "objectBoundingBox")) != "userSpaceOnUse":
            if target is None:
                raise ValueError("this pattern is sized relative to the painted element; pass its box, "
                                 "or use pattern_units='userSpaceOnUse'")
            box = BBox(target.x + box.x * target.width, target.y + box.y * target.height,
                       box.width * target.width, box.height * target.height)
        if box.width <= 0 or box.height <= 0:
            raise ValueError("the pattern tile has no area; give it width and height")
        return box

    def _tile_document(self, tile: BBox) -> Any:
        from ...document import Document

        doc = Document(tile.width, tile.height)
        view = self.get("viewBox")
        doc.root.set("viewBox", view if view is not None else f"0 0 {tile.width} {tile.height}")
        for child in self:
            doc.add(child.clone())
        return doc

    def to_image(self, *, scale: float = 1.0, target: BBox | None = None) -> Image:
        """One tile rendered into an ``<image>`` placed at the tile's position.

        Parameters
        ----------
        scale : float, optional
            Pixels per user unit. Defaults to 1.0.
        target : BBox, optional
            Box of the painted element, for ``objectBoundingBox`` sizes. Defaults to None.

        Returns
        -------
        Image
            The tile's pixels; ``Pattern.from_image`` turns it back into a pattern.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dots = svg.Pattern(svg.circle(2, 2, 1), width=4, height=4, pattern_units="userSpaceOnUse")
        >>> dots.to_image(scale=4).shape
        (16, 16)
        """
        from ..structure import Image

        tile = self.tile(target)
        pixels = self._tile_document(tile).rasterize(scale=scale)
        return Image(pixels, tile.x, tile.y, tile.width, tile.height)

    @classmethod
    def from_image(cls, image: Image, **kwargs: Any) -> Pattern:
        """A pattern whose tile is *image* (its ``x``, ``y``, ``width`` and ``height``), in user units.

        Parameters
        ----------
        image : Image
            The tile; it is copied, so the original stays where it is.
        **kwargs
            More pattern attributes (``pattern_transform``, ``id``, ...).

        Returns
        -------
        Pattern
            A ``userSpaceOnUse`` pattern repeating the image.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> tile = svg.Image(np.zeros((8, 8, 3)), width=4, height=4)
        >>> svg.Pattern.from_image(tile).tile()
        BBox(x=0.0, y=0.0, width=4.0, height=4.0)
        """
        box = image.bounds() or BBox(0.0, 0.0, 0.0, 0.0)
        copy = image.clone()
        copy.translate(-box.x, -box.y)
        kwargs.setdefault("pattern_units", "userSpaceOnUse")
        return cls(copy, x=box.x, y=box.y, width=box.width, height=box.height, **kwargs)

    def tiles(self, area: BBox, *, target: BBox | None = None) -> Group:
        """Copies of the tile content covering *area*, as plain vector graphics.

        Parameters
        ----------
        area : BBox
            The region to cover, in the painted element's user space.
        target : BBox, optional
            Box of the painted element, for ``objectBoundingBox`` sizes. Defaults to None.

        Returns
        -------
        Group
            A ``<g>`` carrying ``patternTransform`` with one ``<g>`` per tile.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dots = svg.Pattern(svg.circle(2, 2, 1), width=4, height=4, pattern_units="userSpaceOnUse")
        >>> len(dots.tiles(svg.BBox(0, 0, 8, 8)))
        4
        """
        from ..structure import Group

        tile = self.tile(target)
        inverse = self.t.inverse()
        corners = [inverse.apply(x, y) for x in (area.left, area.right) for y in (area.top, area.bottom)]
        box = BBox.from_points(corners)
        first_x, last_x = math.floor((box.left - tile.x) / tile.width), math.ceil((box.right - tile.x) / tile.width)
        first_y, last_y = math.floor((box.top - tile.y) / tile.height), math.ceil((box.bottom - tile.y) / tile.height)
        content = self._tile_document(tile).root
        content.discard("width")
        content.discard("height")
        group = Group(transform=self.t) if self.get(self.transform_attribute) is not None else Group()
        for row in range(first_y, last_y):
            for column in range(first_x, last_x):
                cell = content.clone()
                cell.set("x", tile.x + column * tile.width)
                cell.set("y", tile.y + row * tile.height)
                cell.set("width", tile.width)
                cell.set("height", tile.height)
                group.add(cell)
        return group
