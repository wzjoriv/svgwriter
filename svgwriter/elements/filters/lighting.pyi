from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias
from ..._internal._typing import FillRule, LineCap, LineJoin, Opacity
from ...attributes.length import LengthLike
from ...attributes.style import StyleLike
from ...color.color import Color
from ...color.paint import PaintValue
from .._behavior import CoreAttributes
from .._behavior._mixins import XmlSpace
from ..core import Category, Child, ContentModel
from ..core._element import AttrValue, Element
from .base import FilterInput, SingleInput

__all__ = [
    "FeDiffuseLighting",
    "FeDistantLight",
    "FePointLight",
    "FeSpecularLighting",
    "FeSpotLight",
    "LightSource",
    "Vector3",
]

Vector3: TypeAlias = tuple[float, float, float]

class LightSource(CoreAttributes, ABC, category=Category.LIGHT_SOURCE, content=ContentModel.ELEMENTS):
    @property
    @abstractmethod
    def directional(self) -> bool: ...
    @abstractmethod
    def light_vector(
        self,
        x: float,
        y: float,
        z: float,
    ) -> Vector3: ...

class FeDistantLight(LightSource, tag='feDistantLight'):
    def __init__(
        self,
        azimuth: float = 0,
        elevation: float = 0,
        *,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @property
    def directional(self) -> bool: ...
    def light_vector(
        self,
        x: float,
        y: float,
        z: float,
    ) -> Vector3: ...

class FePointLight(LightSource, tag='fePointLight'):
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        *,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @property
    def directional(self) -> bool: ...
    def light_vector(
        self,
        x: float,
        y: float,
        z: float,
    ) -> Vector3: ...

class FeSpotLight(FePointLight, tag='feSpotLight'):
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        *,
        points_at_x: float = 0,
        points_at_y: float = 0,
        points_at_z: float = 0,
        specular_exponent: float | None = None,
        limiting_cone_angle: float | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class _Lighting(SingleInput):
    def __init__(
        self,
        *light: Child,
        surface_scale: float | None = None,
        kernel_unit_length: float | tuple[float, float] | None = None,
        lighting_color: Color | str | None = None,
        in_: FilterInput | None = None,
        result: str | None = None,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        width: LengthLike | None = None,
        height: LengthLike | None = None,
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
    @property
    def light(self) -> LightSource | None: ...

class FeDiffuseLighting(_Lighting, tag='feDiffuseLighting'):
    def __init__(
        self,
        *light: Child,
        diffuse_constant: float | None = None,
        surface_scale: float | None = None,
        kernel_unit_length: float | tuple[float, float] | None = None,
        lighting_color: Color | str | None = None,
        in_: FilterInput | None = None,
        result: str | None = None,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        width: LengthLike | None = None,
        height: LengthLike | None = None,
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

class FeSpecularLighting(_Lighting, tag='feSpecularLighting'):
    def __init__(
        self,
        *light: Child,
        specular_constant: float | None = None,
        specular_exponent: float | None = None,
        surface_scale: float | None = None,
        kernel_unit_length: float | tuple[float, float] | None = None,
        lighting_color: Color | str | None = None,
        in_: FilterInput | None = None,
        result: str | None = None,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        width: LengthLike | None = None,
        height: LengthLike | None = None,
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
