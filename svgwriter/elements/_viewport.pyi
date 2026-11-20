from collections.abc import Mapping
from typing import Any, TypeAlias
from ..attributes.length import LengthLike
from ..attributes.viewbox import PreserveAspectRatio, ViewBox
from ..pathdata.data import BBox
from .base import AttrValue, Child, Element

__all__ = ["FitToViewBox", "Positioned", "ViewBoxLike", "positioned_bbox", "user_units"]

ViewBoxLike: TypeAlias = ViewBox | tuple[float, float, float, float] | str

def user_units(value: Any) -> float: ...

def positioned_bbox(element: Element) -> BBox | None: ...

class FitToViewBox(Element):
    def __init__(
        self,
        *args: Child,
        view_box: ViewBoxLike | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @property
    def view_box(self) -> ViewBox | None: ...
    @view_box.setter
    def view_box(self, value: ViewBoxLike | None) -> None: ...

class Positioned(Element):
    x: Any
    y: Any
    width: Any
    height: Any

    def __init__(
        self,
        *args: Child,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        width: LengthLike | None = None,
        height: LengthLike | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
