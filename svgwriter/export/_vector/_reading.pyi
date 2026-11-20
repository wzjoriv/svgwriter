from dataclasses import dataclass
from typing import Any, Final, TypeAlias
from ...document import Document
from ...transform.matrix import Matrix

__all__ = ["BLACK", "HAIRLINE", "Outline", "Shape", "cmyk_to_rgb", "string_end", "to_document"]

Op: TypeAlias = tuple[str, tuple[float, ...]]
RGB: TypeAlias = tuple[float, float, float]
BLACK: Final = ...
HAIRLINE: Final = ...

@dataclass
class Shape:
    ops: list[Op]
    fill: RGB | None = None
    stroke: RGB | None = None
    fill_opacity: float = 1.0
    stroke_opacity: float = 1.0
    evenodd: bool = False
    stroke_width: float = 1.0
    linecap: str = 'butt'
    linejoin: str = 'miter'
    miter_limit: float = 4.0
    dashes: tuple[float, ...] = ()
    clip: list[Op] | None = None

    def __init__(
        self,
        ops: list[tuple[str, tuple[float, ...]]],
        fill: tuple[float, float, float] | None = None,
        stroke: tuple[float, float, float] | None = None,
        fill_opacity: float = 1.0,
        stroke_opacity: float = 1.0,
        evenodd: bool = False,
        stroke_width: float = 1.0,
        linecap: str = 'butt',
        linejoin: str = 'miter',
        miter_limit: float = 4.0,
        dashes: tuple[float, ...] = (),
        clip: list[tuple[str, tuple[float, ...]]] | None = None,
    ) -> None: ...
    @property
    def visible(self) -> bool: ...

class Outline:
    ops: list[Op]
    current: tuple[float, float] | None
    start: tuple[float, float] | None

    def __init__(self) -> None: ...
    def move(
        self,
        matrix: Matrix,
        x: float,
        y: float,
    ) -> None: ...
    def line(
        self,
        matrix: Matrix,
        x: float,
        y: float,
    ) -> None: ...
    def curve(self, matrix: Matrix, *coords: float) -> None: ...
    def close(self) -> None: ...
    def rect(
        self,
        matrix: Matrix,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None: ...
    def arc(
        self,
        matrix: Matrix,
        center: tuple[float, float],
        radii: tuple[float, float],
        start: float,
        sweep: float,
        *,
        connect: bool = True,
    ) -> None: ...
    def user_current(self, matrix: Matrix) -> tuple[float, float] | None: ...
    def copy(self) -> Outline: ...
    def take(self) -> list[Op]: ...

def cmyk_to_rgb(
    c: float,
    m: float,
    y: float,
    k: float,
) -> RGB: ...

def string_end(data: bytes, start: int) -> int: ...

def to_document(shapes: list[Any], view: tuple[float, float, float, float] | None = None) -> Document: ...
