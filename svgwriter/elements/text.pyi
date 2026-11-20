from collections.abc import Iterator, Mapping, Sequence
from enum import Flag
from typing import Any, ClassVar, TypeAlias, overload
from .._internal._typing import FillRule, LengthAdjust, LineCap, LineJoin, Opacity
from ..attributes.length import LengthLike
from ..attributes.style import StyleLike
from ..color.paint import PaintValue
from ..ops.text import GlyphBox
from ..pathdata.data import BBox, PathData
from ._character import Character, CharacterRange
from ._geometry import PathOperand
from ._mixins import (
    ConditionalAttributes,
    CoreAttributes,
    GraphicsElement,
    PresentationAttributes,
    XLinkAttributes,
    XmlSpace,
)
from .base import AttrValue, Category, Child, ContentModel, Element
from .container import Container
from .shapes import Path
from .structure import Group

__all__ = [
    "AltGlyph",
    "AltGlyphDef",
    "AltGlyphItem",
    "GlyphRef",
    "TRef",
    "TSpan",
    "Text",
    "TextDecoration",
    "TextPath",
]

Coordinates: TypeAlias = LengthLike | Sequence[LengthLike]

class TextDecoration(Flag):
    NONE = 0
    UNDERLINE = 1
    OVERLINE = 2
    LINE_THROUGH = 4
    BLINK = 8

    def svg_value(self, precision: int = 4) -> str: ...

class _TextPositioning(Element):
    def __init__(
        self,
        *args: Child,
        x: Coordinates | None = None,
        y: Coordinates | None = None,
        dx: Coordinates | None = None,
        dy: Coordinates | None = None,
        rotate: float | Sequence[float] | None = None,
        decoration=None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @property
    def text_content(self) -> str: ...
    @text_content.setter
    def text_content(self, value: str) -> None: ...

class _TextLength(Element):
    def __init__(
        self,
        *args: Child,
        text_length: LengthLike | None = None,
        length_adjust: LengthAdjust | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class Text(PathOperand, GraphicsElement, _TextLength, _TextPositioning, tag='text', category=Category.TEXT_CONTENT, content=ContentModel.MIXED):
    geometry_attributes: ClassVar[frozenset[str]]

    @property
    def characters(self) -> str: ...
    def layout(self) -> list[GlyphBox]: ...
    def local_bbox(self) -> BBox | None: ...
    def local_outline(self) -> PathData: ...
    def __len__(self) -> int: ...
    @overload
    def __getitem__(self, index: int) -> Character: ...
    @overload
    def __getitem__(self, index: slice) -> CharacterRange: ...
    def __iter__(self) -> Iterator[Character]: ...
    def run_style(self, source: Element) -> dict[str, object]: ...
    def runs(self) -> list[Path]: ...
    def glyphs(self, *, skip_blank: bool = False) -> Group: ...
    def span(
        self,
        text: str,
        *,
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
    ) -> TSpan: ...

class TSpan(PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextLength, _TextPositioning, tag='tspan', category=Category.TEXT_CONTENT, content=ContentModel.MIXED):
    ...

class TRef(XLinkAttributes, PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextPositioning, tag='tref', category=Category.TEXT_CONTENT):
    def __init__(
        self,
        href: str | Element | None = None,
        *,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
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
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        x: Coordinates | None = None,
        y: Coordinates | None = None,
        dx: Coordinates | None = None,
        dy: Coordinates | None = None,
        rotate: float | Sequence[float] | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class TextPath(XLinkAttributes, PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextLength, tag='textPath', category=Category.TEXT_CONTENT, content=ContentModel.MIXED):
    def __init__(
        self,
        *content: Child,
        href: str | Element | None = None,
        start_offset: LengthLike | None = None,
        method: str | None = None,
        spacing: str | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
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
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        text_length: LengthLike | None = None,
        length_adjust: LengthAdjust | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class AltGlyph(XLinkAttributes, PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextPositioning, tag='altGlyph', category=Category.TEXT_CONTENT, content=ContentModel.TEXT):
    def __init__(
        self,
        text: str = '',
        *,
        href: str | Element | None = None,
        glyph_ref: str | None = None,
        format: str | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
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
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        x: Coordinates | None = None,
        y: Coordinates | None = None,
        dx: Coordinates | None = None,
        dy: Coordinates | None = None,
        rotate: float | Sequence[float] | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class GlyphRef(XLinkAttributes, PresentationAttributes, CoreAttributes, tag='glyphRef', category=Category.TEXT_CONTENT, content=ContentModel.EMPTY):
    def __init__(
        self,
        href: str | Element | None = None,
        *,
        glyph_ref: str | None = None,
        format: str | None = None,
        x: float | None = None,
        y: float | None = None,
        dx: float | None = None,
        dy: float | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
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

class AltGlyphItem(CoreAttributes, Container[GlyphRef], tag='altGlyphItem', category=Category.TEXT_CONTENT):
    ...

class AltGlyphDef(CoreAttributes, Container[Element], tag='altGlyphDef', category=Category.TEXT_CONTENT):
    ...
