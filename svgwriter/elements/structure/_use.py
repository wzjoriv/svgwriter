"""
Reference resolution and geometry for ``<use>``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._internal._typing import Self
from ...attributes.names import PRESENTATION_ATTRIBUTES
from ...pathdata.data import BBox, PathData
from ...transform.matrix import Matrix
from .._geometry import PathOperand
from .._viewport import positioned_bbox, user_units
from ..base import Element

if TYPE_CHECKING:
    from ..shapes import Path


def _symbol_outline(symbol: Element, use: Element) -> PathData:
    """A ``<symbol>``'s children as one outline, its ``viewBox`` fitted into the ``<use>``'s width and height."""
    from ...attributes.viewbox import PreserveAspectRatio, ViewBox
    from ...ops._layers import _fit
    from .._geometry import union_outline

    data = union_outline(symbol)
    box = symbol.get("viewBox")
    if box is None:
        return data
    view = box if isinstance(box, ViewBox) else ViewBox.parse(str(box))
    width = user_units(use.get("width")) or view.width
    height = user_units(use.get("height")) or view.height
    ratio_text = symbol.get("preserveAspectRatio")
    ratio = ratio_text if isinstance(ratio_text, PreserveAspectRatio) else (
        PreserveAspectRatio.parse(str(ratio_text)) if ratio_text is not None else PreserveAspectRatio())
    fit = _fit(width, height, view.width, view.height, ratio)
    return data.transformed(fit @ Matrix.translate(-view.min_x, -view.min_y))


class UseGeometry:
    """Referenced element, bounds and outline of a ``<use>``; mixed into :class:`~svgwriter.elements.structure.Use`."""

    __slots__ = ()

    @classmethod
    def of(cls, element: Element, **kwargs: Any) -> Self:
        """Create a ``<use>`` referencing an element.

        Parameters
        ----------
        element : Element
            The element to reference; it gets an id if it has none.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Use
            The new instance.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Use.of(svg.Rect(0, 0, 5, 5, id="r"), y=2))
        '<use xmlns:xlink="http://www.w3.org/1999/xlink" y="2" xlink:href="#r"/>'
        """
        return cls(element, **kwargs)

    def referenced(self) -> Element | None:
        """The element this ``<use>`` renders, if it can be found.

        Found through the reference itself when the target was given as an
        element (so it works before both are in a document), otherwise by id
        in this element's tree.

        Returns
        -------
        Element or None
            The target element, or None when it cannot be resolved.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dot = svg.circle(0, 0, 2, id="dot")
        >>> svg.Use(dot).referenced() is dot
        True
        """
        target = getattr(self.attributes.get("xlink:href"), "element", None)
        if isinstance(target, Element):
            return target
        return self.root().get_element_by_id(self.target) if self.target else None

    def local_bbox(self) -> BBox | None:
        """Box of the referenced element, moved by ``x``/``y``.

        Returns
        -------
        BBox or None
            The box of the target at this position, or None when the target
            cannot be resolved or has no extent.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Use(svg.circle(0, 0, 2), x=10, y=20).local_bbox()
        BBox(x=8.0, y=18.0, width=4.0, height=4.0)
        """
        box = positioned_bbox(self)
        if box is not None:
            return box
        from .._transformable import Transformable

        target = self.referenced()
        inner = target.bounds() if isinstance(target, Transformable) else None
        if inner is None:
            return None
        return BBox(inner.x + user_units(self.get("x")), inner.y + user_units(self.get("y")), inner.width, inner.height)

    def to_path(self, **kwargs: Any) -> Path:
        """Convert the referenced outline to a ``<path>``.

        The target's own presentation attributes win; anything it does not
        set is inherited from the ``<use>``.

        Parameters
        ----------
        **kwargs
            Attributes to set on the resulting path.

        Returns
        -------
        Path
            The offset outline, styled as SVG renders it.

        Raises
        ------
        TypeError
            If the reference does not resolve to an element with an outline.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.Rect(0, 0, 5, 5, id="r", fill="red")
        >>> doc = svg.Svg(svg.Defs(r), svg.Use(r, x=3, stroke="blue"))
        >>> str(doc.find("use").to_path())
        '<path d="M3 0 L8 0 L8 5 L3 5 Z" stroke="blue" fill="red"/>'
        """
        path = super().to_path()
        target = self.referenced()
        if isinstance(target, PathOperand):
            path.attributes.update(
                (k, v) for k, v in target.attributes.items()
                if k in PRESENTATION_ATTRIBUTES and k not in target.geometry_attributes and k != "clip-path"
            )
        path.update(**kwargs)
        return path

    def local_outline(self) -> PathData:
        """Outline of the referenced element, moved by ``x``/``y``.

        Returns
        -------
        PathData
            The target's outline translated to this position.

        Raises
        ------
        TypeError
            If the target cannot be resolved or has no outline.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Use(svg.circle(0, 0, 2), x=10, y=20).local_outline().bbox
        BBox(x=8.0, y=18.0, width=4.0, height=4.0)
        """
        target = self.referenced()
        offset = Matrix.translate(user_units(self.get("x")), user_units(self.get("y")))
        if target is not None and target.tag == "symbol":
            return _symbol_outline(target, self).transformed(offset)
        if not isinstance(target, PathOperand):
            raise TypeError(f"<use> refers to {'nothing' if target is None else '<' + target.tag + '>'}, which has no outline")
        return target.outline().transformed(offset)
