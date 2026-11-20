from collections.abc import Mapping, Sequence
from typing import Any
from ..._internal._typing import FillRule, LineCap, LineJoin, Opacity, Self
from ...attributes.length import LengthLike
from ...attributes.style import StyleLike
from ...color.paint import PaintValue
from ...pathdata.builder import PathBuilder
from ...pathdata.data import PathData
from .._behavior import CoreAttributes, PresentationAttributes
from .._behavior._mixins import XmlSpace
from ..core import Category, Child, Container, ContentModel, Element
from ..core._element import AttrValue
from ._fonts import Glyph

__all__ = ["FontGlyphs"]

class _GlyphBase(PresentationAttributes, CoreAttributes, Container[Element], category=Category.FONT):
    def __init__(
        self,
        *children: Child,
        d: PathData | PathBuilder | str | None = None,
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

class _Kern(CoreAttributes, category=Category.FONT, content=ContentModel.EMPTY):
    def __init__(
        self,
        k: float,
        *,
        u1: str | None = None,
        g1: str | None = None,
        u2: str | None = None,
        g2: str | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @classmethod
    def pair(
        cls,
        first: str,
        second: str,
        k: float,
        *,
        g1: str | None = None,
        g2: str | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Self: ...

class FontGlyphs:
    def glyph(
        self,
        unicode: str,
        d: PathData | PathBuilder | str,
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
    ) -> Glyph: ...
    def glyphs(self) -> dict[str, Glyph]: ...
