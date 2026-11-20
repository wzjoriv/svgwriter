from .._internal._typing import Self
from .data import PathData

__all__ = ["ShapeCommands"]

class ShapeCommands:
    def extend(self, data: PathData | str) -> Self: ...
    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
    ) -> Self: ...
    def regular_polygon(
        self,
        cx: float,
        cy: float,
        radius: float,
        sides: int,
        rotation: float = -90.0,
    ) -> Self: ...
