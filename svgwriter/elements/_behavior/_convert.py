"""
``Convertible``: conversions and clipping shared by every graphics element.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from ..._internal._constants import SVG_NS, XLINK_NS
from ...attributes.length import Length
from ..core import Element
from ._constants import DEFAULT_STROKE_WIDTH
from ._transformable import Transformable

if TYPE_CHECKING:
    import numpy as np

    from ...color.color import ColorLike
    from ...pathdata.data import BBox
    from ..paint import ClipPath
    from ..shapes import Path
    from ..structure import Group, Image

__all__ = ["Convertible"]

E = TypeVar("E", bound="Convertible")


class Convertible(Transformable):
    """Conversions (``to_path``, ``to_group``, ``rasterize``) and ``clip``.

    Every conversion returns a new element or array and leaves this one
    unchanged. A conversion that cannot be done raises ``TypeError`` naming
    the element and the alternatives.

    See Also
    --------
    svgwriter.elements.Transformable : Transforms and anchors.

    Examples
    --------
    >>> import svgwriter as svg
    >>> box = svg.rect(0, 0, 10, 5, fill="red")
    >>> type(box.to_path()).__name__
    'Path'
    >>> box.rasterize().shape
    (5, 10, 4)
    """

    def to_path(self, **kwargs: Any) -> Path:
        """An equivalent ``<path>``.

        Shapes override this to return their outline; the base implementation
        is for elements that have none.

        Parameters
        ----------
        **kwargs
            Options understood by the overriding implementations.

        Returns
        -------
        Path
            A new ``<path>`` element.

        Raises
        ------
        TypeError
            When the element has no vector outline (an ``<image>``, for
            instance).

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.circle(5, 5, 2).to_path().tag
        'path'
        """
        raise TypeError(
            f"<{self.tag}> has no vector outline and cannot become a path; "
            "use rasterize() for pixels or bounds() for its box"
        )

    def to_group(self, **kwargs: Any) -> Group:
        """A ``<g>`` holding a copy of this element; keywords become group attributes.

        A group returns a copy of itself.

        Parameters
        ----------
        **kwargs
            Attributes set on the group.

        Returns
        -------
        Group
            A new ``<g>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.circle(5, 5, 2).to_group(opacity=0.5)
        >>> g.tag, len(g)
        ('g', 1)
        """
        from ..structure import Group

        if isinstance(self, Group):
            group = self.clone()
            group.update(**kwargs)
            return group
        return Group(self.clone(), **kwargs)

    def to_image(self, *, scale: float = 1.0, padding: float = 0.0, background: ColorLike | None = None) -> Image:
        """Rasterize into an ``<image>`` placed over this element's bounds.

        Parameters
        ----------
        scale : float, optional
            Pixels per user unit. Defaults to 1.0.
        padding : float, optional
            Extra margin in user units. Defaults to 0.0.
        background : color, optional
            Painted under the element. Defaults to None (transparent).

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
            ``clipPathUnits`` for a new clip path. Defaults to None.

        Returns
        -------
        Convertible
            This element.

        Raises
        ------
        TypeError
            If no shape is given.

        See Also
        --------
        unclip : Remove the clip.

        Notes
        -----
        :meth:`to_path` (or :meth:`flatten_clip`) bakes the clip into one
        path with a boolean intersection.

        Examples
        --------
        >>> import svgwriter as svg
        >>> art = svg.rect(0, 0, 100, 100, fill="teal").clip(svg.circle(50, 50, 40))
        >>> art.clip_region.tag
        'clipPath'
        """
        from ..paint import ClipPath

        if not shapes:
            raise TypeError("clip() needs at least one shape; use unclip() to remove the clip")
        if len(shapes) == 1 and isinstance(shapes[0], ClipPath):
            region = shapes[0]
        else:
            region = ClipPath(*shapes, clip_path_units=units)
        self.set("clip-path", region)
        return self

    def unclip(self: E) -> E:
        """Remove the clip and return ``self``.

        Returns
        -------
        Convertible
            This element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> art = svg.rect(0, 0, 9, 9).clip(svg.circle(4, 4, 3)).unclip()
        >>> art.clip_region is None
        True
        """
        self.discard("clip-path")
        return self

    @property
    def clip_region(self) -> ClipPath | None:
        """The ``<clipPath>`` this element is clipped by, if it can be found.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 9, 9).clip_region is None
        True
        """
        from ..._internal._tree import resolve
        from ..paint import ClipPath

        region = resolve(self, self.attributes.get("clip-path"))
        return region if isinstance(region, ClipPath) else None

    def render_bounds(self) -> BBox | None:
        """:meth:`bounds` grown by half the stroke width.

        Returns
        -------
        BBox or None
            The box including the stroke, or None when :meth:`bounds` is unknown.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 10, 10, stroke="black", stroke_width=2).render_bounds()
        BBox(x=-1.0, y=-1.0, width=12.0, height=12.0)
        """
        box = self.bounds()
        if box is None:
            return None
        stroke = self.get("stroke")
        half = 0.0
        if stroke is not None and str(stroke) != "none":
            half = Length.parse(self.get("stroke-width", DEFAULT_STROKE_WIDTH)).to_user_units() / 2
        return type(box)(box.x - half, box.y - half, box.width + 2 * half, box.height + 2 * half)

    def rasterize(
        self, *, scale: float = 1.0, pixels: tuple[int, int] | int | None = None, padding: float = 0.0,
        background: ColorLike | None = None,
    ) -> np.ndarray:
        """Render this element alone into an RGBA array.

        The canvas is the element's :meth:`render_bounds` in parent
        coordinates, plus *padding* on every side.

        Parameters
        ----------
        scale : float, optional
            Pixels per user unit. Defaults to 1.0.
        pixels : (int, int) or int, optional
            Exact output ``(columns, rows)``, or one int for a square; the
            element is fitted and centred, and *scale* is ignored. Defaults to None.
        padding : float, optional
            Extra margin in user units. Defaults to 0.0.
        background : color, optional
            Painted under the element. Defaults to None (transparent).

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
        box = self.render_bounds()
        if box is None:
            raise TypeError(f"<{self.tag}> has no known size; give it width and height or rasterize the document")
        canvas = type(box)(box.x - padding, box.y - padding, box.width + 2 * padding, box.height + 2 * padding)
        if pixels is not None:
            canvas, scale = _fit(canvas, (pixels, pixels) if isinstance(pixels, int) else pixels)
        return render_box(self, canvas, scale, background)


def _fit(box: BBox, size: tuple[int, int]) -> tuple[BBox, float]:
    """Grow *box* about its centre to the aspect of *size*; return it with the matching scale."""
    columns, rows = size
    scale = min(columns / box.width, rows / box.height) if box.width and box.height else 1.0
    width, height = columns / scale, rows / scale
    return type(box)(box.x - (width - box.width) / 2, box.y - (height - box.height) / 2, width, height), scale


def render_box(element: Element, box: BBox, scale: float, background: ColorLike | None = None) -> np.ndarray:
    """Render *element* alone onto the canvas *box* (parent coordinates) as straight RGBA.

    Parameters
    ----------
    element : Element
        The element to draw; any definitions it references are carried along.
    box : BBox
        The canvas rectangle in the element's parent coordinates.
    scale : float
        Pixels per user unit.
    background : str, optional
        Color painted under the element. Defaults to None (transparent).

    Returns
    -------
    numpy.ndarray
        ``float32`` array, shape ``(rows, columns, 4)``, straight RGBA in ``0..1``.

    See Also
    --------
    Convertible.rasterize : Render an element on its own bounds.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.elements._behavior._convert import render_box
    >>> render_box(svg.rect(0, 0, 4, 4, fill="red"), svg.BBox(0, 0, 8, 4), 1.0).shape
    (4, 8, 4)
    """
    from ...io.writer import to_string
    from ...ops.render import render_tree
    from ...transform.matrix import Matrix

    x, y, width, height = box.x, box.y, box.width, box.height
    defs = "".join(to_string(d, xml_declaration=False, pretty=False) for d in _definitions(element))

    def wrap(body: str) -> str:
        return (
            f'<svg xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}" '
            f'viewBox="{x} {y} {width} {height}" width="{width}" height="{height}">'
            f"<defs>{defs}</defs>{body}</svg>"
        )

    return render_tree(element, wrap, width, height, view=Matrix.translate(-x, -y), scale=scale, background=background)


def _to_image(element: Convertible, scale: float, padding: float, background: ColorLike | None) -> Image:
    from ..structure import Image

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
