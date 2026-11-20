from typing import Any
from ..._internal._typing import Self
from ...pathdata.data import BBox

__all__ = ["RectConstructors"]

class RectConstructors:
    @classmethod
    def square(
        cls,
        size: float,
        *,
        center: tuple[float, float] | None = None,
        **kwargs: Any,
    ) -> Self: ...
    @classmethod
    def from_bbox(cls, box: BBox, **kwargs: Any) -> Self: ...
    @classmethod
    def from_corners(
        cls,
        first: tuple[float, float],
        second: tuple[float, float],
        **kwargs: Any,
    ) -> Self: ...
    @classmethod
    def from_center(
        cls,
        center: tuple[float, float],
        size: tuple[float, float],
        **kwargs: Any,
    ) -> Self: ...
