from collections.abc import Iterable, Mapping, Sequence
from typing import Any, ClassVar, overload
from numpy import ndarray
from ..._internal._typing import FillRule, LineCap, LineJoin, Opacity, Self
from ...attributes.length import LengthLike
from ...attributes.style import StyleLike
from ...color.paint import PaintValue
from ...pathdata.builder import PathBuilder
from ...pathdata.data import BBox, PathData, PathDataLike
from ...transform.transform import TransformLike
from .._behavior._geometry import Operand
from .._behavior._mixins import XmlSpace
from .._behavior._transformable import PointLike
from ..core._element import AttrValue, Element
from ..structure import Group
from ._base import Shape
from ._commands import PathCommands

__all__ = ["Path"]

class Path(PathCommands, Shape, tag='path'):
    geometry_attributes: ClassVar[frozenset[str]]
    path_length: float | None

    def __init__(
        self,
        d: PathDataLike | PathBuilder = '',
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
    ) -> None: ...
    @property
    def d(self) -> PathData: ...
    @d.setter
    def d(self, value: PathDataLike | PathBuilder) -> None: ...
    @property
    def nodes(self) -> ndarray: ...
    @nodes.setter
    def nodes(self, value: object) -> None: ...
    @classmethod
    def from_points(
        cls,
        points: Iterable[tuple[float, float]],
        *,
        closed: bool = False,
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
    ) -> Self: ...
    @property
    def bbox(self) -> BBox: ...
    def local_outline(self) -> PathData: ...
    @overload
    def __add__(self, other: Path | PathData | str) -> Path: ...
    @overload
    def __add__(self, other: Element | Iterable[Element]) -> Group: ...
    def __iadd__(self, other: Path | PathData | str) -> Self: ...
    def __ior__(self, other: Operand) -> Self: ...
    def __iand__(self, other: Operand) -> Self: ...
    def __isub__(self, other: Operand) -> Self: ...
    def __ixor__(self, other: Operand) -> Self: ...
