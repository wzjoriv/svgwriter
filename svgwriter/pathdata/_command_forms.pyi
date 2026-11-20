from abc import ABC, abstractmethod
from typing import Any, ClassVar
from .._internal._typing import Self
from ..transform.matrix import Point

__all__ = ["CommandForms", "PathCommand", "XYEnd"]

class CommandForms:
    code: ClassVar[str]
    coordinates: ClassVar[tuple[str, ...]]
    relative: bool
    arguments: Any

    @property
    def letter(self) -> str: ...
    def to_absolute(self, current: Point) -> Self: ...
    def svg_value(self, precision: int = 4) -> str: ...
    def __str__(self) -> str: ...

class XYEnd:
    x: float
    y: float
    relative: bool

    def end_point(self, current: Point, start: Point) -> Point: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...

class PathCommand(CommandForms, ABC):
    code: ClassVar[str]
    coordinates: ClassVar[tuple[str, ...]]
    relative: bool

    @property
    @abstractmethod
    def arguments(self) -> tuple[float, ...]: ...
    @abstractmethod
    def end_point(self, current: Point, start: Point) -> Point: ...
