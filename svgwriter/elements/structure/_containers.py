"""``svg``, ``g``, ``defs``, ``symbol``, ``use``, ``switch`` and ``a``."""

from __future__ import annotations

from typing import Any

from ..._internal._constants import SVG_VERSION
from ..._internal._typing import Self
from ...attributes.length import LengthLike
from ...path.data import BBox, PathData
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
    version : str
        Written as the ``version`` attribute; ``None`` omits it.
    base_profile, zoom_and_pan, content_style_type : str, optional
        The remaining ``<svg>``-specific attributes.
    **kwargs
        Position, viewBox, presentation, conditional and core attributes.
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
        """A root sized ``width`` x ``height`` with a matching viewBox."""
        kwargs.setdefault("view_box", (0, 0, width, height))
        return cls(width=width, height=height, **kwargs)

    def defs(self) -> Defs:
        """The first ``<defs>`` child, created on demand."""
        for child in self:
            if isinstance(child, Defs):
                return child
        return self.insert(0, Defs())


class Group(PathOperand, GraphicsElement, GraphicsContainer, tag="g", category=Category.CONTAINER):
    """``<g>``: groups elements to share attributes and a transform."""

    def local_bbox(self) -> BBox | None:
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the children's outlines."""
        return union_outline(self)


class Defs(GraphicsElement, GraphicsContainer, tag="defs", category=Category.CONTAINER):
    """``<defs>``: referenced, never directly rendered, content."""


class Symbol(
    FitToViewBox,
    ExternalResourcesAttribute,
    PresentationAttributes,
    CoreAttributes,
    GraphicsContainer,
    tag="symbol",
    category=Category.STRUCTURAL,
):
    """``<symbol>``: a template instantiated by ``<use>``."""


class Use(PathOperand, GraphicsElement, XLinkAttributes, Positioned, tag="use", category=Category.STRUCTURAL):
    """``<use>``: renders a referenced element."""

    def __init__(self, href: str | Element | None = None, x: LengthLike | None = None, y: LengthLike | None = None, **kwargs: Any) -> None:
        super().__init__(href=href, x=x, y=y, **kwargs)

    @classmethod
    def of(cls, element: Element, **kwargs: Any) -> Self:
        """Reference *element*, giving it an id if it has none."""
        return cls(element, **kwargs)

    def local_bbox(self) -> BBox | None:
        box = positioned_bbox(self)
        if box is not None:
            return box
        from .._transformable import Transformable

        target = self.root().get_element_by_id(self.target) if self.target else None
        inner = target.bounds() if isinstance(target, Transformable) else None
        if inner is None:
            return None
        return BBox(inner.x + user_units(self.get("x")), inner.y + user_units(self.get("y")), inner.width, inner.height)

    def local_outline(self) -> PathData:
        """The referenced element's outline, offset by ``x``/``y``."""
        target = self.root().get_element_by_id(self.target) if self.target else None
        if not isinstance(target, PathOperand):
            raise TypeError(f"<use> refers to {'nothing' if target is None else '<' + target.tag + '>'}, which has no outline")
        return target.outline().transformed(Matrix.translate(user_units(self.get("x")), user_units(self.get("y"))))


class Switch(PathOperand, GraphicsElement, GraphicsContainer, tag="switch", category=Category.CONTAINER):
    """``<switch>``: renders the first child whose conditions pass."""

    def local_bbox(self) -> BBox | None:
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the children's outlines."""
        return union_outline(self)


class A(PathOperand, GraphicsElement, XLinkAttributes, GraphicsContainer, tag="a", category=Category.CONTAINER):
    """``<a>``: a hyperlink around graphics."""

    def __init__(self, *children: Child, href: str | Element | None = None, target: str | None = None, **kwargs: Any) -> None:
        super().__init__(*children, href=href, **kwargs)
        self.update(target=target)

    def local_bbox(self) -> BBox | None:
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the children's outlines."""
        return union_outline(self)
