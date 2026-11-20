from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar
from ..transform.matrix import Point
from ._command_forms import CommandForms, XYEnd

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

class PathCommand(CommandForms, ABC):
    code: ClassVar[str]
    coordinates: ClassVar[tuple[str, ...]]
    relative: bool

    @property
    @abstractmethod
    def arguments(self) -> tuple[float, ...]: ...
    @abstractmethod
    def end_point(self, current: Point, start: Point) -> Point: ...

@dataclass(frozen=True)
class MoveTo(XYEnd, PathCommand):
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
class LineTo(XYEnd, PathCommand):
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
class CurveTo(XYEnd, PathCommand):
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
class SmoothCurveTo(XYEnd, PathCommand):
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
class QuadTo(XYEnd, PathCommand):
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
class SmoothQuadTo(XYEnd, PathCommand):
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
class ArcTo(XYEnd, PathCommand):
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
