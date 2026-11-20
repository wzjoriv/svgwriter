from collections.abc import Iterable, Mapping, Sequence
from typing import Any
from .._internal._typing import FillRule, LineCap, LineJoin, Opacity, Self
from ..attributes.length import LengthLike
from ..attributes.style import StyleLike
from ..color.color import Color
from ..color.paint import PaintValue
from ._mixins import XmlSpace
from .base import AttrValue, Element
from .paint import Stop, StopSpec

__all__ = ["GradientStops"]

class GradientStops:
    def add_stop(
        self,
        offset: float,
        color: Color | str,
        opacity: Opacity | None = None,
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
        display: str | None = None,
        visibility: str | None = None,
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
    ) -> Stop: ...
    @classmethod
    def from_colors(cls, colors: Sequence[Color | str], **kwargs: Any) -> Self: ...
    @classmethod
    def from_stops(cls, stops: Iterable[StopSpec], **kwargs: Any) -> Self: ...
