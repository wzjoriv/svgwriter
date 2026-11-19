"""``svg``, ``g``, ``defs``, ``symbol``, ``use``, ``switch`` and ``a``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..._internal._constants import SVG_VERSION
from ..._internal._typing import Self
from ...attributes.length import LengthLike
from ...attributes.names import PRESENTATION_ATTRIBUTES
from ...pathdata.data import BBox, PathData
from ...transform.matrix import Matrix
from .._geometry import PathOperand, union_outline
from .._mixins import (
    ConditionalAttributes,
    CoreAttributes,
    ExternalResourcesAttribute,
    GraphicsElement,
    PresentationAttributes,
    XLinkAttributes,
)
from .._transformable import children_bbox
from .._viewport import FitToViewBox, Positioned, positioned_bbox, user_units
from ..base import Category, Child, Element
from ..container import GraphicsContainer

if TYPE_CHECKING:
    from ..shapes import Path

__all__ = ["A", "Defs", "Group", "Svg", "Switch", "Symbol", "Use"]


class Svg(
    Positioned,
    FitToViewBox,
    ExternalResourcesAttribute,
    PresentationAttributes,
    ConditionalAttributes,
    CoreAttributes,
    GraphicsContainer,
    tag="svg",
    category=Category.STRUCTURAL,
):
    """``<svg>``: a document root or nested viewport.

    Parameters
    ----------
    *children : Element
        Initial content.
    version : str, optional
        Written as the ``version`` attribute; ``None`` omits it. Defaults to
        the SVG version the library targets (``"1.1"``).
    base_profile, zoom_and_pan, content_style_type : str, optional
        The remaining ``<svg>``-specific attributes. Defaults to None.
    **kwargs
        Position (``x``, ``y``, ``width``, ``height``), ``view_box``,
        presentation, conditional and core attributes in Python spelling.

    See Also
    --------
    Group : Group content without establishing a viewport.
    Symbol : A reusable viewport instantiated by ``<use>``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Svg(svg.Circle(5, 5, 3), width=10, height=10))
    '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" version="1.1"><circle cx="5" cy="5" r="3"/></svg>'
    """

    def __init__(
        self,
        *children: Child,
        version: str | None = SVG_VERSION,
        base_profile: str | None = None,
        zoom_and_pan: str | None = None,
        content_style_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*children, **kwargs)
        self.update(
            version=version,
            base_profile=base_profile,
            zoom_and_pan=zoom_and_pan,
            content_style_type=content_style_type,
        )

    @classmethod
    def with_size(cls, width: float, height: float, **kwargs: Any) -> Self:
        """Create a root with a size and a matching viewBox.

        Parameters
        ----------
        width, height : float
            Size in user units; the viewBox is ``0 0 width height`` unless
            `view_box` is passed in `kwargs`.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Svg
            The new root.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Svg.with_size(100, 50))
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50" viewBox="0 0 100 50" version="1.1"/>'
        """
        kwargs.setdefault("view_box", (0, 0, width, height))
        return cls(width=width, height=height, **kwargs)

    def defs(self) -> Defs:
        """Return the first ``<defs>`` child, creating one if needed.

        A new ``<defs>`` is inserted before all other children.

        Returns
        -------
        Defs
            The existing or newly created ``<defs>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Svg()
        >>> doc.defs() is doc.defs()
        True
        >>> str(doc)
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"><defs/></svg>'
        """
        for child in self:
            if isinstance(child, Defs):
                return child
        return self.insert(0, Defs())


class Group(PathOperand, GraphicsElement, GraphicsContainer, tag="g", category=Category.CONTAINER):
    """``<g>``: groups elements to share attributes and a transform.

    Parameters
    ----------
    *children : Element
        Initial content.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Svg : A group that also establishes a viewport.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Group(svg.Rect(0, 0, 5, 5), fill="red"))
    '<g fill="red"><rect x="0" y="0" width="5" height="5"/></g>'
    """

    def local_bbox(self) -> BBox | None:
        """The union of the children's bounding boxes, or None when empty."""
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the children's outlines."""
        return union_outline(self)


class Defs(GraphicsElement, GraphicsContainer, tag="defs", category=Category.CONTAINER):
    """``<defs>``: referenced, never directly rendered, content.

    Parameters
    ----------
    *children : Element
        Initial content.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Use : Instantiate an element defined here.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Defs(svg.Circle(5, 5, 3, id="dot")))
    '<defs><circle id="dot" cx="5" cy="5" r="3"/></defs>'
    """


class Symbol(
    FitToViewBox,
    ExternalResourcesAttribute,
    PresentationAttributes,
    CoreAttributes,
    GraphicsContainer,
    tag="symbol",
    category=Category.STRUCTURAL,
):
    """``<symbol>``: a template instantiated by ``<use>``.

    Parameters
    ----------
    *children : Element
        Initial content.
    **kwargs
        ``view_box``, ``preserve_aspect_ratio``, presentation and core
        attributes in Python spelling.

    See Also
    --------
    Use : Instantiate the symbol.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Symbol(svg.Circle(5, 5, 3), id="dot", view_box=(0, 0, 10, 10)))
    '<symbol id="dot" viewBox="0 0 10 10"><circle cx="5" cy="5" r="3"/></symbol>'
    """


class Use(PathOperand, GraphicsElement, XLinkAttributes, Positioned, tag="use", category=Category.STRUCTURAL):
    """``<use>``: renders a referenced element.

    Parameters
    ----------
    href : str or Element, optional
        The target as a reference string or the element itself, which gets
        an id if it has none. Defaults to None.
    x, y : length, optional
        Translation applied to the instance. Defaults to None.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Defs : Where referenced content usually lives.
    Symbol : A viewport template to instantiate.

    Examples
    --------
    >>> import svgwriter as svg
    >>> dot = svg.Circle(5, 5, 3, id="dot")
    >>> str(svg.Use(dot, x=10))
    '<use xmlns:xlink="http://www.w3.org/1999/xlink" x="10" xlink:href="#dot"/>'
    """

    def __init__(self, href: str | Element | None = None, x: LengthLike | None = None, y: LengthLike | None = None, **kwargs: Any) -> None:
        super().__init__(href=href, x=x, y=y, **kwargs)

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

    def local_bbox(self) -> BBox | None:
        """The bounding box of the referenced element at this position, or None if unresolved."""
        box = positioned_bbox(self)
        if box is not None:
            return box
        from .._transformable import Transformable

        target = self.root().get_element_by_id(self.target) if self.target else None
        inner = target.bounds() if isinstance(target, Transformable) else None
        if inner is None:
            return None
        return BBox(inner.x + user_units(self.get("x")), inner.y + user_units(self.get("y")), inner.width, inner.height)

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"x", "y", "width", "height", "xlink:href"})

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
        '<path d="M3 0 L8 0 L8 5 L3 5 L3 0 Z" stroke="blue" fill="red"/>'
        """
        path = super().to_path()
        target = self.root().get_element_by_id(self.target) if self.target else None
        if isinstance(target, PathOperand):
            path.attributes.update(
                (k, v) for k, v in target.attributes.items()
                if k in PRESENTATION_ATTRIBUTES and k not in target.geometry_attributes and k != "clip-path"
            )
        path.update(**kwargs)
        return path

    def local_outline(self) -> PathData:
        """The referenced element's outline, offset by ``x``/``y``."""
        target = self.root().get_element_by_id(self.target) if self.target else None
        if not isinstance(target, PathOperand):
            raise TypeError(f"<use> refers to {'nothing' if target is None else '<' + target.tag + '>'}, which has no outline")
        return target.outline().transformed(Matrix.translate(user_units(self.get("x")), user_units(self.get("y"))))


class Switch(PathOperand, GraphicsElement, GraphicsContainer, tag="switch", category=Category.CONTAINER):
    """``<switch>``: renders the first child whose conditions pass.

    Parameters
    ----------
    *children : Element
        Initial content.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Switch(svg.Rect(0, 0, 5, 5, required_extensions="x")))
    '<switch><rect x="0" y="0" width="5" height="5" requiredExtensions="x"/></switch>'
    """

    def local_bbox(self) -> BBox | None:
        """The union of the children's bounding boxes, or None when empty."""
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the children's outlines."""
        return union_outline(self)


class A(PathOperand, GraphicsElement, XLinkAttributes, GraphicsContainer, tag="a", category=Category.CONTAINER):
    """``<a>``: a hyperlink around graphics.

    Parameters
    ----------
    *children : Element
        Initial content.
    href : str or Element, optional
        The link target. Defaults to None.
    target : str, optional
        Where to open the link, such as ``"_blank"``. Defaults to None.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.A(svg.Rect(0, 0, 5, 5), href="https://example.com"))
    '<a xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://example.com"><rect x="0" y="0" width="5" height="5"/></a>'
    """

    def __init__(self, *children: Child, href: str | Element | None = None, target: str | None = None, **kwargs: Any) -> None:
        super().__init__(*children, href=href, **kwargs)
        self.update(target=target)

    def local_bbox(self) -> BBox | None:
        """The union of the children's bounding boxes, or None when empty."""
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the children's outlines."""
        return union_outline(self)
