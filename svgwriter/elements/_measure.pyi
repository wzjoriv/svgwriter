from typing import Any
from ..ops.measure import Cap, Join
from ..pathdata.data import BBox
from ..transform.matrix import Point
from .shapes import Path

__all__ = ["Measurement"]

class Measurement:
    def simplified(self) -> Path: ...
    def stroked(
        self,
        width: float | None = None,
        *,
        cap: Cap | None = None,
        join: Join | None = None,
        miter_limit: float | None = None,
    ) -> Path: ...
    def exact_bbox(self) -> BBox: ...
    def contains_point(self, x: Any, y: float | None = None) -> Any: ...
    def total_length(self) -> float: ...
    def point_at_length(self, distance: float) -> Point: ...
