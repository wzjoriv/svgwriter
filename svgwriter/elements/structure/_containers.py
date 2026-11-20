"""
``svg``, ``g``, ``defs``, ``symbol``, ``use``, ``switch`` and ``a``.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ..._internal._constants import SVG_VERSION
from ..._internal._typing import Self
from ...attributes.length import LengthLike
from ...pathdata.data import BBox, PathData
from .._behavior import (
    ConditionalAttributes,
    CoreAttributes,
    ExternalResourcesAttribute,
    FitToViewBox,
    GraphicsElement,
    PathOperand,
    Positioned,
    PresentationAttributes,
    XLinkAttributes,
    children_bbox,
    union_outline,
)
from ..core import Category, Child, Element, GraphicsContainer
from ._use import UseGeometry

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
        from ...attributes.length import Length

        if isinstance(width, Length) or isinstance(height, Length):
            first = width if isinstance(width, Length) else Length(float(width))
            second = Length.parse(height).to(first.unit) if first.absolute else Length.parse(height)
            kwargs.setdefault("view_box", (0, 0, first.value, second.value))
        else:
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
        """Box around the group's children.

        Returns
        -------
        BBox or None
            The union of the children's bounding boxes, or None when empty.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Group(svg.rect(0, 0, 5, 5), svg.rect(10, 10, 5, 5)).local_bbox()
        BBox(x=0.0, y=0.0, width=15.0, height=15.0)
        """
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the group's children's outlines.

        Returns
        -------
        PathData
            The combined outline of every child.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Group(svg.rect(0, 0, 5, 5), svg.rect(10, 10, 5, 5)).local_outline().bbox
        BBox(x=0.0, y=0.0, width=15.0, height=15.0)
        """
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


class Use(
    UseGeometry,
    PathOperand,
    GraphicsElement,
    XLinkAttributes,
    Positioned,
    tag="use",
    category=Category.STRUCTURAL,
):
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

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"x", "y", "width", "height", "xlink:href"})


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
        """Box around the switch's children.

        Returns
        -------
        BBox or None
            The union of the children's bounding boxes, or None when empty.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Switch(svg.rect(0, 0, 5, 5)).local_bbox()
        BBox(x=0.0, y=0.0, width=5.0, height=5.0)
        """
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the switch's children's outlines.

        Returns
        -------
        PathData
            The combined outline of every child.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Switch(svg.rect(0, 0, 5, 5)).local_outline().bbox
        BBox(x=0.0, y=0.0, width=5.0, height=5.0)
        """
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
        """Box around the link's children.

        Returns
        -------
        BBox or None
            The union of the children's bounding boxes, or None when empty.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.A(svg.rect(0, 0, 5, 5), href="#x").local_bbox()
        BBox(x=0.0, y=0.0, width=5.0, height=5.0)
        """
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the link's children's outlines.

        Returns
        -------
        PathData
            The combined outline of every child.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.A(svg.rect(0, 0, 5, 5), href="#x").local_outline().bbox
        BBox(x=0.0, y=0.0, width=5.0, height=5.0)
        """
        return union_outline(self)
