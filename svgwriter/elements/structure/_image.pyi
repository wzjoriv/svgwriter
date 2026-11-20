from collections.abc import Mapping, Sequence
from os import PathLike
from typing import Any
from numpy import ndarray
from ..._internal._typing import FillRule, LineCap, LineJoin, Opacity
from ...attributes.length import LengthLike
from ...attributes.style import StyleLike
from ...attributes.viewbox import PreserveAspectRatio
from ...color.paint import PaintValue
from ...pathdata.data import BBox
from ...transform.transform import TransformLike
from .._mixins import GraphicsElement, XLinkAttributes, XmlSpace
from .._transformable import PointLike
from .._viewport import Positioned
from ..base import AttrValue, Category, ContentModel, Element
from ._compositing import Compositing
from ._pixels import Pixels

__all__ = ["Image"]

class Image(Compositing, GraphicsElement, XLinkAttributes, Positioned, tag='image', category=Category.GRAPHICS, content=ContentModel.ELEMENTS):
    def __init__(
        self,
        source: ndarray | str | None = None,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        width: LengthLike | None = None,
        height: LengthLike | None = None,
        *,
        alpha: ndarray | float | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        href: str | Element | None = None,
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
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @classmethod
    def open(
        cls,
        path: str | PathLike[str],
        *,
        source: ndarray | str | None = None,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        width: LengthLike | None = None,
        height: LengthLike | None = None,
        alpha: ndarray | float | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        href: str | Element | None = None,
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
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Image: ...
    @property
    def pixels(self) -> Pixels | None: ...
    @property
    def color(self) -> ndarray: ...
    @color.setter
    def color(self, value: ndarray) -> None: ...
    @property
    def alpha(self) -> ndarray | float: ...
    @alpha.setter
    def alpha(self, value: ndarray | float) -> None: ...
    @property
    def shape(self) -> tuple[int, int]: ...
    def rgba(self) -> ndarray: ...
    def encode(
        self,
        format: str = 'png',
        *,
        quality: int = 90,
    ) -> bytes: ...
    def local_bbox(self) -> BBox | None: ...
