from collections.abc import Mapping, Sequence
from typing import Any, Literal, TypeAlias
from .._internal._typing import FillRule, LineCap, LineJoin, Opacity, Units
from ..attributes.length import LengthLike
from ..attributes.style import StyleLike
from ..attributes.viewbox import PreserveAspectRatio
from ..color.paint import PaintValue
from ..pathdata.data import BBox, PathData
from ..transform.transform import TransformLike
from ._geometry import PathOperand
from ._mixins import (
    ConditionalAttributes,
    CoreAttributes,
    ExternalResourcesAttribute,
    PresentationAttributes,
    Transformable,
    XmlSpace,
)
from ._transformable import PointLike
from ._viewport import FitToViewBox, Positioned, ViewBoxLike
from .base import AttrValue, Category, Child, Element
from .container import GraphicsContainer

__all__ = ["ClipPath", "Marker", "MarkerOrient", "Mask"]

MarkerOrient: TypeAlias = float | Literal['auto']

class ClipPath(PathOperand, Transformable, PresentationAttributes, ConditionalAttributes, ExternalResourcesAttribute, CoreAttributes, GraphicsContainer, tag='clipPath', category=Category.CONTAINER):
    def __init__(
        self,
        *children: Child,
        clip_path_units: Units | None = None,
        t: TransformLike | None = None,
        transform: TransformLike | None = None,
        anchor: PointLike | None = None,
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
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    def local_bbox(self) -> BBox | None: ...
    def local_outline(self) -> PathData: ...

class Mask(Positioned, PresentationAttributes, ConditionalAttributes, ExternalResourcesAttribute, CoreAttributes, GraphicsContainer, tag='mask', category=Category.CONTAINER):
    def __init__(
        self,
        *children: Child,
        mask_units: Units | None = None,
        mask_content_units: Units | None = None,
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
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class Marker(FitToViewBox, PresentationAttributes, ExternalResourcesAttribute, CoreAttributes, GraphicsContainer, tag='marker', category=Category.CONTAINER):
    def __init__(
        self,
        *children: Child,
        ref_x: float = 0,
        ref_y: float = 0,
        marker_width: LengthLike | None = None,
        marker_height: LengthLike | None = None,
        marker_units: Literal['strokeWidth', 'userSpaceOnUse'] | None = None,
        orient: MarkerOrient | None = None,
        view_box: ViewBoxLike | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
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
