from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any
from ..._internal._typing import FillRule, LineCap, LineJoin, Opacity, Self
from ...attributes.length import LengthLike
from ...attributes.style import StyleLike
from ...color.paint import PaintValue
from .._behavior import CoreAttributes
from .._behavior._mixins import XmlSpace
from ..core import Container, ContentModel
from ..core._element import AttrValue, Element
from .base import FilterInput, SingleInput

__all__ = [
    "FeComponentTransfer",
    "FeFunc",
    "FeFuncA",
    "FeFuncB",
    "FeFuncG",
    "FeFuncR",
    "TransferType",
]

class TransferType(str, Enum):
    IDENTITY = 'identity'
    TABLE = 'table'
    DISCRETE = 'discrete'
    LINEAR = 'linear'
    GAMMA = 'gamma'

class FeFunc(CoreAttributes, content=ContentModel.ELEMENTS):
    def __init__(
        self,
        type: TransferType = TransferType.IDENTITY,
        *,
        table_values: Sequence[float] | None = None,
        slope: float | None = None,
        intercept: float | None = None,
        amplitude: float | None = None,
        exponent: float | None = None,
        offset: float | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @classmethod
    def linear(
        cls,
        slope: float,
        intercept: float = 0,
        *,
        table_values: Sequence[float] | None = None,
        amplitude: float | None = None,
        exponent: float | None = None,
        offset: float | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Self: ...
    @classmethod
    def table(
        cls,
        *values: float,
        slope: float | None = None,
        intercept: float | None = None,
        amplitude: float | None = None,
        exponent: float | None = None,
        offset: float | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Self: ...
    @classmethod
    def gamma(
        cls,
        amplitude: float = 1,
        exponent: float = 1,
        offset: float = 0,
        *,
        table_values: Sequence[float] | None = None,
        slope: float | None = None,
        intercept: float | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Self: ...
    def evaluate(self, c: float) -> float: ...

class FeFuncR(FeFunc, tag='feFuncR'):
    ...

class FeFuncG(FeFunc, tag='feFuncG'):
    ...

class FeFuncB(FeFunc, tag='feFuncB'):
    ...

class FeFuncA(FeFunc, tag='feFuncA'):
    ...

class FeComponentTransfer(SingleInput, Container[FeFunc], tag='feComponentTransfer'):
    def __init__(
        self,
        *functions: FeFunc,
        red: FeFunc | None = None,
        green: FeFunc | None = None,
        blue: FeFunc | None = None,
        alpha: FeFunc | None = None,
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
