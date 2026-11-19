"""``Convertible``: conversions and clipping shared by every graphics element."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, TypeVar

from .._internal._constants import SVG_NS, XLINK_NS
from ..attributes.length import Length
from ._transformable import Transformable
from .base import Element

if TYPE_CHECKING:
    import numpy as np

    from ..pathdata.data import BBox
    from .clip import ClipPath
    from .shapes import Path
    from .structure import Group, Image

__all__ = ["Convertible"]

E = TypeVar("E", bound="Convertible")
DEFAULT_STROKE_WIDTH: Final = 1.0


class Convertible(Transformable):
    """Conversions (``to_path``, ``to_group``, ``rasterize``) and ``clip``.

    Every conversion returns a new element or array and leaves this one
    unchanged. A conversion that cannot be done raises ``TypeError`` naming
    the element and the alternatives.
    """

    def to_path(self, **kwargs: Any) -> Path:
        """An equivalent ``<path>``.

        Raises
        ------
        TypeError
            When the element has no vector outline (an ``<image>``, for
            instance).
        """
        raise TypeError(
            f"<{self.tag}> has no vector outline and cannot become a path; "
            "use rasterize() for pixels or bounds() for its box"
        )

    def to_group(self, **kwargs: Any) -> Group:
        """A ``<g>`` holding a copy of this element; keywords become group attributes.

        A group returns a copy of itself.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.circle(5, 5, 2).to_group(opacity=0.5)
        >>> g.tag, len(g)
        ('g', 1)
        """
        from .structure import Group

        if isinstance(self, Group):
            group = self.clone()
            group.update(**kwargs)
            return group
        return Group(self.clone(), **kwargs)

    def to_image(self, *, scale: float = 1.0, padding: float = 0.0, background: str | None = None) -> Image:
        """Rasterize into an ``<image>`` placed over this element's bounds.

        Parameters
        ----------
        scale : float
            Pixels per user unit.
        padding : float
            Extra margin in user units.
        background : color, optional
            Painted under the element; transparent when omitted.

        Returns
        -------
        Image
            Embedded pixels positioned where the element was drawn.

        Examples
        --------
        >>> import svgwriter as svg
        >>> img = svg.circle(10, 10, 5, fill="red").to_image(scale=2)
        >>> img.shape, (img.x, img.y, img.width)
        ((20, 20), (5.0, 5.0, 10.0))
        """
        return _to_image(self, scale, padding, background)

    def clip(self: E, *shapes: Element, units: str | None = None) -> E:
        """Clip to the union of *shapes* (or a ``ClipPath``) and return ``self``.

        Shapes are in this element's local coordinates, so the clip moves
        with the element. The ``<clipPath>`` goes into ``<defs>`` when the
        element is in a document.

        Parameters
        ----------
        *shapes : Element
            Shapes, text or ``<use>``; a single :class:`ClipPath` is used as is.
        units : {"userSpaceOnUse", "objectBoundingBox"}, optional
            ``clipPathUnits`` for a new clip path.

        Examples
        --------
        >>> import svgwriter as svg
        >>> art = svg.rect(0, 0, 100, 100, fill="teal").clip(svg.circle(50, 50, 40))
        >>> art.clip_region.tag
        'clipPath'

        Notes
        -----
        :meth:`to_path` (or :meth:`flatten_clip`) bakes the clip into one
        path with a boolean intersection.
        """
        from .clip import ClipPath

        if not shapes:
            raise TypeError("clip() needs at least one shape; use unclip() to remove the clip")
        if len(shapes) == 1 and isinstance(shapes[0], ClipPath):
            region = shapes[0]
        else:
            region = ClipPath(*shapes, clip_path_units=units)
        self.set("clip-path", region)
        return self

    def unclip(self: E) -> E:
        """Remove the clip and return ``self``."""
        self.discard("clip-path")
        return self

    @property
    def clip_region(self) -> ClipPath | None:
        """The ``<clipPath>`` this element is clipped by, if it can be found."""
        from ._geometry import resolve
        from .clip import ClipPath

        region = resolve(self, self.attributes.get("clip-path"))
        return region if isinstance(region, ClipPath) else None

    def render_bounds(self) -> BBox | None:
        """:meth:`bounds` grown by half the stroke width."""
        box = self.bounds()
        if box is None:
            return None
        stroke = self.get("stroke")
        half = 0.0
        if stroke is not None and str(stroke) != "none":
            half = Length.parse(self.get("stroke-width", DEFAULT_STROKE_WIDTH)).to_user_units() / 2
        return type(box)(box.x - half, box.y - half, box.width + 2 * half, box.height + 2 * half)

    def rasterize(
        self, *, scale: float = 1.0, padding: float = 0.0, background: str | None = None
    ) -> np.ndarray:
        """Render this element alone into an RGBA array.

        The canvas is the element's :meth:`render_bounds` in parent
        coordinates, plus *padding* on every side.

        Parameters
        ----------
        scale : float
            Pixels per user unit.
        padding : float
            Extra margin in user units.
        background : color, optional
            Painted under the element; transparent when omitted.

        Returns
        -------
        numpy.ndarray
            ``float32`` array, shape ``(rows, columns, 4)``, straight RGBA in ``0..1``.

        Raises
        ------
        TypeError
            When the element's size is unknown (an ``<image>`` without width
            and height, for instance).

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 8, 4, fill="red").rasterize(scale=2).shape
        (8, 16, 4)
        """
        from ..io.writer import to_string
        from ..ops.render import render_tree
        from ..transform.matrix import Matrix

        box = self.render_bounds()
        if box is None:
            raise TypeError(f"<{self.tag}> has no known size; give it width and height or rasterize the document")
        x, y = box.x - padding, box.y - padding
        width, height = box.width + 2 * padding, box.height + 2 * padding
        defs = "".join(to_string(d, xml_declaration=False, pretty=False) for d in _definitions(self))

        def wrap(body: str) -> str:
            return (
                f'<svg xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}" '
                f'viewBox="{x} {y} {width} {height}" width="{width}" height="{height}">'
                f"<defs>{defs}</defs>{body}</svg>"
            )

        return render_tree(self, wrap, width, height, view=Matrix.translate(-x, -y), scale=scale,
                           background=background)


def _to_image(element: Convertible, scale: float, padding: float, background: str | None) -> Image:
    from .structure import Image

    box = element.render_bounds()
    pixels = element.rasterize(scale=scale, padding=padding, background=background)
    assert box is not None
    return Image(pixels, box.x - padding, box.y - padding, box.width + 2 * padding, box.height + 2 * padding)


def _definitions(element: Element) -> list[Element]:
    """Elements *element* needs from outside its subtree: the root ``<defs>`` and unplaced references."""
    found: list[Element] = []
    root = element.root()
    if root.tag == "svg" and root is not element:
        found.extend(child for child in root if child.tag == "defs")
    pending = [element]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        for item in node.iter():
            for value in item.attributes.values():
                target = getattr(value, "element", None)
                if isinstance(target, Element) and target.parent is None and id(target) not in seen:
                    seen.add(id(target))
                    found.append(target)
                    pending.append(target)
    return found
