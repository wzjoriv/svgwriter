from dataclasses import dataclass
from ._reading import RGB
from ._tikz_syntax import Pair, Point

@dataclass(frozen=True)
class _Place:
    x: float
    y: float
    shape: str = 'rectangle'
    half_width: float = 0.0
    half_height: float = 0.0

    def __init__(
        self,
        x: float,
        y: float,
        shape: str = 'rectangle',
        half_width: float = 0.0,
        half_height: float = 0.0,
    ) -> None: ...
    def anchor(self, name: str) -> Point: ...

@dataclass
class _Context:
    colors: dict[str, RGB]
    styles: dict[str, list[Pair]]
    places: dict[str, _Place] = ...

    def __init__(
        self,
        colors: dict[str, RGB],
        styles: dict[str, list[Pair]],
        places: dict[str, _Place] = ...,
    ) -> None: ...
