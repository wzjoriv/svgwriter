from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar
from .matrix import Matrix

__all__ = ["MatrixOp", "Rotate", "Scale", "SkewX", "SkewY", "TransformOp", "Translate"]

class TransformOp(ABC):
    keyword: ClassVar[str]

    @property
    @abstractmethod
    def arguments(self) -> tuple[float, ...]: ...
    @abstractmethod
    def to_matrix(self) -> Matrix: ...
    def svg_value(self, precision: int = 4) -> str: ...
    def __str__(self) -> str: ...

@dataclass(frozen=True)
class Translate(TransformOp):
    keyword: ClassVar[str] = 'translate'
    tx: float
    ty: float = 0.0

    def __init__(self, tx: float, ty: float = 0.0) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...
    def to_matrix(self) -> Matrix: ...

@dataclass(frozen=True)
class Scale(TransformOp):
    keyword: ClassVar[str] = 'scale'
    sx: float
    sy: float | None = None

    def __init__(self, sx: float, sy: float | None = None) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...
    def to_matrix(self) -> Matrix: ...

@dataclass(frozen=True)
class Rotate(TransformOp):
    keyword: ClassVar[str] = 'rotate'
    angle: float
    cx: float = 0.0
    cy: float = 0.0

    def __init__(
        self,
        angle: float,
        cx: float = 0.0,
        cy: float = 0.0,
    ) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...
    def to_matrix(self) -> Matrix: ...

@dataclass(frozen=True)
class SkewX(TransformOp):
    keyword: ClassVar[str] = 'skewX'
    angle: float

    def __init__(self, angle: float) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...
    def to_matrix(self) -> Matrix: ...

@dataclass(frozen=True)
class SkewY(TransformOp):
    keyword: ClassVar[str] = 'skewY'
    angle: float

    def __init__(self, angle: float) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...
    def to_matrix(self) -> Matrix: ...

@dataclass(frozen=True)
class MatrixOp(TransformOp):
    keyword: ClassVar[str] = 'matrix'
    matrix: Matrix

    def __init__(self, matrix: Matrix) -> None: ...
    @property
    def arguments(self) -> tuple[float, ...]: ...
    def to_matrix(self) -> Matrix: ...
