from dataclasses import dataclass
from ..transform.matrix import Point

__all__ = ["CenterArc", "endpoint_to_center"]

@dataclass(frozen=True)
class CenterArc:
    cx: float
    cy: float
    rx: float
    ry: float
    rotation: float
    start_angle: float
    sweep: float

    def __init__(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        rotation: float,
        start_angle: float,
        sweep: float,
    ) -> None: ...
    def point_at(self, t: float) -> Point: ...
    def sample(self, count: int) -> list[Point]: ...

def endpoint_to_center(
    start: Point,
    end: Point,
    rx: float,
    ry: float,
    rotation: float,
    large_arc: bool,
    sweep: bool,
) -> CenterArc | None: ...
