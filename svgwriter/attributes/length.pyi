from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeAlias, overload

__all__ = [
    "Length",
    "LengthLike",
    "LengthUnit",
    "Unit",
    "cm",
    "em",
    "ex",
    "inch",
    "mm",
    "pc",
    "percent",
    "pt",
    "px",
]

class Unit(str, Enum):
    NONE = ''
    PX = 'px'
    PT = 'pt'
    PC = 'pc'
    MM = 'mm'
    CM = 'cm'
    IN = 'in'
    EM = 'em'
    EX = 'ex'
    PERCENT = '%'
    USER = NONE
    PIXEL = PX
    INCH = IN

    def __str__(self) -> str: ...

@dataclass(frozen=True, slots=True)
class Length:
    value: float
    unit: Unit = Unit.NONE

    def __init__(self, value: float, unit: Unit = Unit.NONE) -> None: ...
    @overload
    @classmethod
    def parse(cls, text: str) -> Length: ...
    @overload
    @classmethod
    def parse(cls, text: float) -> Length: ...
    @overload
    @classmethod
    def parse(cls, text: Length) -> Length: ...
    def to_user_units(
        self,
        *,
        dpi: float = 96.0,
        font_size: float = 16.0,
        reference: float | None = None,
    ) -> float: ...
    def svg_value(self, precision: int = 4) -> str: ...
    def __str__(self) -> str: ...
    def __float__(self) -> float: ...
    @property
    def absolute(self) -> bool: ...
    def to(self, unit: Unit | str) -> Length: ...
    def __add__(self, other: Length | float | str) -> Length: ...
    def __radd__(self, other: float) -> Length: ...
    def __sub__(self, other: Length | float | str) -> Length: ...
    def __rsub__(self, other: float) -> Length: ...
    def __mul__(self, factor: float) -> Length: ...
    def __rmul__(self, factor: float) -> Length: ...
    def __truediv__(self, other: float | Length) -> Any: ...
    def __neg__(self) -> Length: ...
    def __abs__(self) -> Length: ...
    def __lt__(self, other: Length | float) -> bool: ...
    def __le__(self, other: Length | float) -> bool: ...
    def __gt__(self, other: Length | float) -> bool: ...
    def __ge__(self, other: Length | float) -> bool: ...

LengthLike: TypeAlias = Length | float | int | str

class LengthUnit:
    unit: Unit

    def __init__(self, unit: Unit) -> None: ...
    def __call__(self, value: float) -> Length: ...
    def __rmul__(self, value: float) -> Length: ...
    def __repr__(self) -> str: ...

px: LengthUnit
pt: LengthUnit
pc: LengthUnit
mm: LengthUnit
cm: LengthUnit
inch: LengthUnit
em: LengthUnit
ex: LengthUnit
percent: LengthUnit
