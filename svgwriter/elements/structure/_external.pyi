from collections.abc import Mapping
from typing import Any
from ...attributes.style import StyleSheet
from ...attributes.viewbox import PreserveAspectRatio
from .._behavior import CoreAttributes, ExternalResourcesAttribute, FitToViewBox, XLinkAttributes
from .._behavior._mixins import XmlSpace
from .._behavior._viewport import ViewBoxLike
from ..core import ContentModel
from ..core._element import AttrValue

__all__ = ["ColorProfile", "StyleElement", "View"]

class StyleElement(CoreAttributes, tag='style', content=ContentModel.TEXT):
    def __init__(
        self,
        css: str | StyleSheet = '',
        *,
        type: str = 'text/css',
        media: str | None = None,
        title: str | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @property
    def css(self) -> str: ...
    @css.setter
    def css(self, value: str | StyleSheet) -> None: ...

class View(FitToViewBox, ExternalResourcesAttribute, CoreAttributes, tag='view', content=ContentModel.EMPTY):
    def __init__(
        self,
        *,
        view_target: str | None = None,
        zoom_and_pan: str | None = None,
        view_box: ViewBoxLike | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class ColorProfile(XLinkAttributes, CoreAttributes, tag='color-profile', content=ContentModel.ELEMENTS):
    def __init__(
        self,
        name: str,
        href: str | None = None,
        *,
        local: str | None = None,
        rendering_intent: str | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
