from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from os import PathLike
from typing import Any, Literal, TypeAlias
from .._internal._typing import FillRule, LineCap, LineJoin, Opacity
from ..attributes.length import LengthLike
from ..attributes.style import StyleLike
from ..color.paint import PaintValue
from ..elements._mixins import XmlSpace
from ..elements.base import AttrValue, Element
from ..elements.shapes import Path
from ..pathdata.data import PathData
from ..transform.transform import TransformLike

__all__ = [
    "Anchor",
    "FontWeight",
    "GlyphBox",
    "glyph_shape",
    "layout_glyphs",
    "register_font",
    "text_outline",
    "text_to_path",
    "text_width",
]

Anchor: TypeAlias = Literal['start', 'middle', 'end']
FontWeight: TypeAlias = int | Literal['normal', 'bold']

def register_font(source: str | PathLike[str] | bytes, family: str | None = None) -> str: ...

def glyph_shape(
    char: str,
    font_family: str,
    size: float,
    weight: FontWeight = 'normal',
    italic: bool = False,
    language: str | None = None,
) -> tuple[PathData, float]: ...

def text_width(
    text: str,
    font_family: str = 'sans-serif',
    size: float = 16.0,
    *,
    weight: FontWeight = 'normal',
    italic: bool = False,
) -> float: ...

def text_outline(
    text: str,
    font_family: str = 'sans-serif',
    size: float = 16.0,
    *,
    x: float = 0.0,
    y: float = 0.0,
    anchor: Anchor = 'start',
    weight: FontWeight = 'normal',
    italic: bool = False,
) -> PathData: ...

@dataclass
class GlyphBox:
    char: str
    outline: PathData
    x: float
    y: float
    angle: float
    advance: float
    source: Any = None

    def __init__(
        self,
        char: str,
        outline: PathData,
        x: float,
        y: float,
        angle: float,
        advance: float,
        source: Any = None,
    ) -> None: ...
    def placed(self) -> PathData: ...

def layout_glyphs(
    text: str,
    font_family: str = 'sans-serif',
    size: float = 16.0,
    *,
    x: Sequence[float] = (0.0,),
    y: Sequence[float] = (0.0,),
    dx: Sequence[float] = (),
    dy: Sequence[float] = (),
    rotate: Sequence[float] = (),
    anchor: Anchor = 'start',
    weight: FontWeight = 'normal',
    italic: bool = False,
) -> list[GlyphBox]: ...

def text_to_path(
    text: str,
    font_family: str = 'sans-serif',
    size: float = 16.0,
    *,
    x: float = 0.0,
    y: float = 0.0,
    anchor: Anchor = 'start',
    weight: FontWeight = 'normal',
    italic: bool = False,
    path_length: float | None = None,
    t: TransformLike | None = None,
    transform: TransformLike | None = None,
    external_resources_required: bool | None = None,
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
    id: str | None = None,
    attrs: Mapping[str, AttrValue] | None = None,
    **kwargs: Any,
) -> Path: ...
