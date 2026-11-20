from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar
from .._internal._typing import Self
from ..transform.matrix import Point

__all__ = [
    "ArcTo",
    "ClosePath",
    "CurveTo",
    "HLineTo",
    "LineTo",
    "MoveTo",
    "PathCommand",
    "QuadTo",
    "SmoothCurveTo",
    "SmoothQuadTo",
    "VLineTo",
]

class PathCommand(ABC):
    code: ClassVar[str]
    coordinates: ClassVar[tuple[str, ...]]
    relative: bool

    @property
    def letter(self) -> str: ...
    @property
    @abstractmethod
    def arguments(self) -> tuple[float, ...]: ...
    @abstractmethod
    def end_point(self, current: Point, start: Point) -> Point: ...
    def to_absolute(self, current: Point) -> Self: ...
    def svg_value(self, precision: int = 4) -> str: ...
    def __str__(self) -> str: ...

@dataclass(frozen=True)
class _XYCommand(PathCommand):
    def __init__(self) -> None: ...
    def end_point(self, current: Point, start: Point) -> Point: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...

@dataclass(frozen=True)
class MoveTo(_XYCommand):
    code: ClassVar[str] = 'M'
    coordinates: ClassVar[tuple[str, ...]] = ('x', 'y')
    x: float
    y: float
    relative: bool = False

    def __init__(
        self,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...

@dataclass(frozen=True)
class LineTo(_XYCommand):
    code: ClassVar[str] = 'L'
    coordinates: ClassVar[tuple[str, ...]] = ('x', 'y')
    x: float
    y: float
    relative: bool = False

    def __init__(
        self,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...

@dataclass(frozen=True)
class HLineTo(PathCommand):
    code: ClassVar[str] = 'H'
    coordinates: ClassVar[tuple[str, ...]] = ('x',)
    x: float
    relative: bool = False

    def __init__(
        self,
        x: float,
        *,
        relative: bool = False,
    ) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...
    def end_point(self, current: Point, start: Point) -> Point: ...

@dataclass(frozen=True)
class VLineTo(PathCommand):
    code: ClassVar[str] = 'V'
    coordinates: ClassVar[tuple[str, ...]] = ('y',)
    y: float
    relative: bool = False

    def __init__(
        self,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...
    def end_point(self, current: Point, start: Point) -> Point: ...

@dataclass(frozen=True)
class CurveTo(_XYCommand):
    code: ClassVar[str] = 'C'
    coordinates: ClassVar[tuple[str, ...]] = ('x1', 'y1', 'x2', 'y2', 'x', 'y')
    x1: float
    y1: float
    x2: float
    y2: float
    x: float
    y: float
    relative: bool = False

    def __init__(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...

@dataclass(frozen=True)
class SmoothCurveTo(_XYCommand):
    code: ClassVar[str] = 'S'
    coordinates: ClassVar[tuple[str, ...]] = ('x2', 'y2', 'x', 'y')
    x2: float
    y2: float
    x: float
    y: float
    relative: bool = False

    def __init__(
        self,
        x2: float,
        y2: float,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...

@dataclass(frozen=True)
class QuadTo(_XYCommand):
    code: ClassVar[str] = 'Q'
    coordinates: ClassVar[tuple[str, ...]] = ('x1', 'y1', 'x', 'y')
    x1: float
    y1: float
    x: float
    y: float
    relative: bool = False

    def __init__(
        self,
        x1: float,
        y1: float,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...

@dataclass(frozen=True)
class SmoothQuadTo(_XYCommand):
    code: ClassVar[str] = 'T'
    coordinates: ClassVar[tuple[str, ...]] = ('x', 'y')
    x: float
    y: float
    relative: bool = False

    def __init__(
        self,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...

@dataclass(frozen=True)
class ArcTo(_XYCommand):
    code: ClassVar[str] = 'A'
    coordinates: ClassVar[tuple[str, ...]] = ('x', 'y')
    rx: float
    ry: float
    rotation: float
    large_arc: bool
    sweep: bool
    x: float
    y: float
    relative: bool = False

    def __init__(
        self,
        rx: float,
        ry: float,
        rotation: float,
        large_arc: bool,
        sweep: bool,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...

@dataclass(frozen=True)
class ClosePath(PathCommand):
    code: ClassVar[str] = 'Z'
    relative: bool = False

    def __init__(self, *, relative: bool = False) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...
    def end_point(self, current: Point, start: Point) -> Point: ...
