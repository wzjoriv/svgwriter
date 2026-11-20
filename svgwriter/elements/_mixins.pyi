from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any
from .._internal._typing import FillRule, LineCap, LineJoin, Opacity
from ..attributes.length import LengthLike
from ..attributes.style import Style, StyleLike
from ..color.paint import PaintValue
from ._convert import Convertible
from ._transformable import Transformable as Transformable
from .base import AttrValue, Child, Element

__all__ = [
    "ConditionalAttributes",
    "CoreAttributes",
    "ExternalResourcesAttribute",
    "GraphicsElement",
    "PresentationAttributes",
    "StyleAttributes",
    "Transformable",
    "XLinkAttributes",
    "XmlSpace",
]

class XmlSpace(str, Enum):
    DEFAULT = 'default'
    PRESERVE = 'preserve'

class CoreAttributes(Element):
    def __init__(
        self,
        *args: Child,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class ConditionalAttributes(Element):
    def __init__(
        self,
        *args: Child,
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class StyleAttributes(Element):
    def __init__(
        self,
        *args: Child,
        class_: str | Sequence[str] | None = None,
        style: StyleLike | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @property
    def classes(self) -> list[str]: ...
    def add_class(self, *names: str) -> None: ...
    @property
    def style(self) -> Style: ...
    @style.setter
    def style(self, value: StyleLike | None) -> None: ...

class PresentationAttributes(StyleAttributes):
    fill: PaintValue | None
    stroke: PaintValue | None
    stroke_width: Any
    opacity: float | None

    def __init__(
        self,
        *args: Child,
        fill: PaintValue = None,
        fill_opacity: Opacity | None = None,
        fill_rule: FillRule | None = None,
        stroke: PaintValue = None,
        stroke_width: LengthLike | None = None,
        stroke_opacity: Opacity | None = None,
        stroke_linecap: LineCap | None = None,
        stroke_linejoin: LineJoin | None = None,
        stroke_miterlimit: float | None = None,
        stroke_dasharray: Sequence[float] | str | None = None,
        stroke_dashoffset: LengthLike | None = None,
        opacity: Opacity | None = None,
        display: str | None = None,
        visibility: str | None = None,
        color: str | None = None,
        clip_path: str | Element | None = None,
        mask: str | Element | None = None,
        filter: str | Element | None = None,
        font_family: str | None = None,
        font_size: LengthLike | None = None,
        font_weight: str | int | None = None,
        text_anchor: str | None = None,
        class_: str | Sequence[str] | None = None,
        style: StyleLike | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    def presentation(self) -> dict[str, Any]: ...
    def to_css(self) -> None: ...
    def from_css(self) -> None: ...

class XLinkAttributes(Element):
    def __init__(
        self,
        *args: Child,
        href: str | Element | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @property
    def href(self) -> Any: ...
    @href.setter
    def href(self, value: Any) -> None: ...
    @property
    def target(self) -> str | None: ...

class ExternalResourcesAttribute(Element):
    def __init__(
        self,
        *args: Child,
        external_resources_required: bool | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class GraphicsElement(Convertible, ExternalResourcesAttribute, PresentationAttributes, ConditionalAttributes, CoreAttributes):
    ...
