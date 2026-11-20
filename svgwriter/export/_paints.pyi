from dataclasses import dataclass
from ..color.color import Color
from ..transform.matrix import Matrix

__all__ = ["Shading"]

@dataclass
class Shading:
    kind: str
    coords: tuple[float, ...]
    stops: list[tuple[float, Color]]
    matrix: Matrix

    def __init__(
        self,
        kind: str,
        coords: tuple[float, ...],
        stops: list[tuple[float, Color]],
        matrix: Matrix,
    ) -> None: ...
