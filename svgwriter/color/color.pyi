from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import TypeAlias
from .._internal._drawable import Drawable
from .._internal._typing import N
from ._blending import ColorBlending
from ._channels import ColorChannels

__all__ = ["Color", "ColorLike", "as_color", "clamp", "parse_color"]

def clamp(
    value: N,
    low: N,
    high: N,
) -> N: ...

@dataclass(frozen=True)
class Color(ColorChannels, ColorBlending, Drawable):
    r: float
    g: float
    b: float
    a: float = 1.0
    icc: str | None = None
    name: str | None = None

    def __init__(
        self,
        r: float,
        g: float,
        b: float,
        a: float = 1.0,
        icc: str | None = None,
        name: str | None = None,
    ) -> None: ...
    def __post_init__(self) -> None: ...
    @classmethod
    def parse(cls, text: str) -> Color: ...
    @classmethod
    def from_uint8(
        cls,
        r: int,
        g: int,
        b: int,
        a: int = 255,
    ) -> Color: ...
    @classmethod
    def from_hsl(
        cls,
        hue: float,
        saturation: float,
        lightness: float,
        alpha: float = 1.0,
    ) -> Color: ...
    def __iter__(self) -> Iterator[float]: ...
    def with_icc(self, spec: str) -> Color: ...
    def to_css(self) -> str: ...
    def svg_value(self, precision: int = 4) -> str: ...
    def __str__(self) -> str: ...

ColorLike: TypeAlias = Color | str | Sequence[float]

def as_color(value: ColorLike) -> Color: ...

def parse_color(text: str) -> Color: ...
