import os
from collections.abc import Iterable
from typing import Annotated, Literal, NamedTuple, NewType, ParamSpec, TypeAlias, TypeVar
from typing_extensions import NotRequired as NotRequired, Required as Required, Self as Self
from ._stack import Stack as Stack

__all__ = [
    "Align",
    "AnyPath",
    "ElementId",
    "FillRule",
    "LengthAdjust",
    "LineCap",
    "LineJoin",
    "Matrix6",
    "N",
    "NotRequired",
    "Number",
    "Opacity",
    "P",
    "Pair",
    "Points",
    "R",
    "Required",
    "Self",
    "SpreadMethod",
    "Stack",
    "T",
    "Units",
    "ValueRange",
]

_T = TypeVar('_T')
Pair: TypeAlias = tuple[_T, _T]
Matrix6: TypeAlias = tuple[float, float, float, float, float, float]

class ValueRange(NamedTuple):
    low: float
    high: float

T = TypeVar('T')
R = TypeVar('R')
P = ParamSpec('P')
N = TypeVar('N', int, float)
Number: TypeAlias = int | float
AnyPath: TypeAlias = str | os.PathLike[str]
Points: TypeAlias = Iterable[tuple[float, float]]
Opacity: TypeAlias = Annotated[float, ValueRange(0.0, 1.0)]
ElementId = NewType('ElementId', str)
LineCap: TypeAlias = Literal['butt', 'round', 'square', 'inherit']
LineJoin: TypeAlias = Literal['miter', 'round', 'bevel', 'inherit']
FillRule: TypeAlias = Literal['nonzero', 'evenodd', 'inherit']
Units: TypeAlias = Literal['userSpaceOnUse', 'objectBoundingBox']
SpreadMethod: TypeAlias = Literal['pad', 'reflect', 'repeat']
LengthAdjust: TypeAlias = Literal['spacing', 'spacingAndGlyphs']
Align: TypeAlias = Literal['none', 'xMinYMin', 'xMidYMin', 'xMaxYMin', 'xMinYMid', 'xMidYMid', 'xMaxYMid', 'xMinYMax', 'xMidYMax', 'xMaxYMax']
