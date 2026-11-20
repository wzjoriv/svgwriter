from dataclasses import dataclass
from ...transform.matrix import Matrix
from ._tikz_syntax import Pair, Point

@dataclass
class _Frame:
    x_unit: float = 28.452755905511808
    y_unit: float = 28.452755905511808
    x_scale: float = 1.0
    y_scale: float = 1.0
    matrix: Matrix = ...

    def __init__(
        self,
        x_unit: float = 28.452755905511808,
        y_unit: float = 28.452755905511808,
        x_scale: float = 1.0,
        y_scale: float = 1.0,
        matrix: Matrix = ...,
    ) -> None: ...
    def vector(self, text: str) -> Point: ...
    def absolute(self, text: str) -> Point: ...
    def scoped(self, pairs: list[Pair]) -> _Frame: ...
    def radii(self, x: str, y: str) -> Point: ...

@dataclass(frozen=True)
class _Scope:
    frame: _Frame
    pairs: list[Pair]

    def __init__(self, frame: _Frame, pairs: list[Pair]) -> None: ...
    def child(self, pairs: list[Pair]) -> _Scope: ...
