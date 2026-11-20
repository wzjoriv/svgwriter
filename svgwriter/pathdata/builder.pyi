from collections.abc import Mapping, Sequence
from typing import Any
from .._internal._typing import FillRule, LineCap, LineJoin, Opacity
from ..attributes.length import LengthLike
from ..attributes.style import StyleLike
from ..color.paint import PaintValue
from ..elements._behavior._mixins import XmlSpace
from ..elements._behavior._transformable import PointLike
from ..elements.core._element import AttrValue, Element
from ..elements.shapes import Path
from ..transform.matrix import Point
from ..transform.transform import TransformLike
from ._builder_curves import CurveCommands
from ._builder_shapes import ShapeCommands
from .data import PathData

__all__ = ["PathBuilder"]

class PathBuilder(CurveCommands, ShapeCommands):
    def __init__(self, start: tuple[float, float] | None = None) -> None: ...
    @property
    def current_point(self) -> Point: ...
    def move_to(
        self,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...
    def line_to(
        self,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...
    def horizontal_to(
        self,
        x: float,
        *,
        relative: bool = False,
    ) -> None: ...
    def vertical_to(
        self,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...
    def close(self) -> None: ...
    def build(self) -> PathData: ...
    def to_element(
        self,
        *,
        path_length: float | None = None,
        t: TransformLike | None = None,
        transform: TransformLike | None = None,
        anchor: PointLike | None = None,
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
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Path: ...
    def __len__(self) -> int: ...
    def __str__(self) -> str: ...
