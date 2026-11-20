from collections.abc import Mapping, Sequence
from typing import Any
from .._internal._typing import FillRule, LineCap, LineJoin, Opacity
from ..attributes.length import LengthLike
from ..attributes.style import StyleLike
from ..color.paint import PaintValue
from ..pathdata.builder import PathBuilder
from ..pathdata.data import PathData
from ._fontbase import FontGlyphs, _GlyphBase, _Kern
from ._mixins import (
    CoreAttributes,
    ExternalResourcesAttribute,
    PresentationAttributes,
    XLinkAttributes,
    XmlSpace,
)
from .base import AttrValue, Category, Child, ContentModel, Element
from .container import Container

__all__ = [
    "Font",
    "FontFace",
    "FontFaceFormat",
    "FontFaceName",
    "FontFaceSrc",
    "FontFaceUri",
    "Glyph",
    "HKern",
    "MissingGlyph",
    "VKern",
]

class Font(FontGlyphs, PresentationAttributes, ExternalResourcesAttribute, CoreAttributes, Container[Element], tag='font', category=Category.FONT):
    def __init__(
        self,
        *children: Child,
        horiz_adv_x: float = 0,
        horiz_origin_x: float | None = None,
        horiz_origin_y: float | None = None,
        vert_origin_x: float | None = None,
        vert_origin_y: float | None = None,
        vert_adv_y: float | None = None,
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
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class Glyph(_GlyphBase, tag='glyph'):
    def __init__(
        self,
        unicode: str | None = None,
        d: PathData | PathBuilder | str | None = None,
        *,
        glyph_name: str | None = None,
        orientation: str | None = None,
        arabic_form: str | None = None,
        lang: str | None = None,
        horiz_adv_x: float | None = None,
        vert_origin_x: float | None = None,
        vert_origin_y: float | None = None,
        vert_adv_y: float | None = None,
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
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class MissingGlyph(_GlyphBase, tag='missing-glyph'):
    ...

class HKern(_Kern, tag='hkern'):
    ...

class VKern(_Kern, tag='vkern'):
    ...

class FontFace(CoreAttributes, Container[Element], tag='font-face', category=Category.FONT):
    def __init__(
        self,
        *children: Child,
        font_family: str | None = None,
        font_style: str | None = None,
        font_variant: str | None = None,
        font_weight: str | None = None,
        font_stretch: str | None = None,
        font_size: str | None = None,
        unicode_range: str | None = None,
        units_per_em: float | None = None,
        ascent: float | None = None,
        descent: float | None = None,
        cap_height: float | None = None,
        x_height: float | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **descriptors: Any,
    ) -> None: ...

class FontFaceSrc(CoreAttributes, Container[Element], tag='font-face-src', category=Category.FONT):
    ...

class FontFaceFormat(CoreAttributes, tag='font-face-format', category=Category.FONT, content=ContentModel.EMPTY):
    def __init__(
        self,
        string: str | None = None,
        *,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class FontFaceUri(XLinkAttributes, CoreAttributes, Container[FontFaceFormat], tag='font-face-uri', category=Category.FONT):
    def __init__(
        self,
        href: str | None = None,
        *formats: FontFaceFormat,
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

class FontFaceName(CoreAttributes, tag='font-face-name', category=Category.FONT, content=ContentModel.EMPTY):
    def __init__(
        self,
        name: str | None = None,
        *,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
