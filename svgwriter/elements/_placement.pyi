from typing import Any
from ..pathdata.data import BBox
from ..transform.matrix import Point
from ._transformable import E, PointLike

__all__ = ["Placement"]

class Placement:
    @property
    def anchor(self) -> Point: ...
    @anchor.setter
    def anchor(self, value: PointLike | None) -> None: ...
    @property
    def position(self) -> Point: ...
    @position.setter
    def position(self, value: PointLike) -> None: ...
    def place(
        self: E,
        x: float,
        y: float,
        *,
        at: str | None = None,
    ) -> E: ...
    def align(
        self: E,
        target: Any,
        at: str = 'center',
        *,
        to: str | None = None,
        offset: PointLike = (0.0, 0.0),
    ) -> E: ...
    def bounds(self) -> BBox | None: ...
