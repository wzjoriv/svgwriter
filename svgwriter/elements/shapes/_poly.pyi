import numpy as np
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar, TypeAlias
from numpy import ndarray
from ..._internal._typing import FillRule, LineCap, LineJoin, Opacity, Self
from ...attributes.length import LengthLike
from ...attributes.style import StyleLike
from ...color.paint import PaintValue
from ...pathdata.data import BBox, PathData
from ...transform.transform import TransformLike
from .._behavior._mixins import XmlSpace
from .._behavior._transformable import PointLike
from ..core._element import AttrValue, Element
from ._base import Shape

__all__ = ["PointList", "PointsLike", "Polygon", "Polyline", "as_points"]

PointsLike: TypeAlias = np.ndarray | Sequence[Sequence[float]]

class PointList:
    array: np.ndarray

    def __init__(self, array: ndarray) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def svg_value(self, precision: int = 4) -> str: ...
    def __repr__(self) -> str: ...

def as_points(value: PointsLike | str) -> ndarray: ...

class Polyline(Shape, tag='polyline'):
    geometry_attributes: ClassVar[frozenset[str]]

    def __init__(
        self,
        points: PointsLike | str = (),
        *,
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
    ) -> None: ...
    @property
    def points(self) -> ndarray: ...
    @points.setter
    def points(self, value: PointsLike | str) -> None: ...
    @classmethod
    def regular(
        cls,
        cx: float,
        cy: float,
        radius: float,
        sides: int = 6,
        *,
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
    ) -> Self: ...
    @property
    def bbox(self) -> BBox: ...
    def local_outline(self) -> PathData: ...

class Polygon(Polyline, tag='polygon'):
    @property
    def area(self) -> float: ...
    def local_outline(self) -> PathData: ...
