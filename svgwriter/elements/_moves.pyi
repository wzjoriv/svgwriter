from typing import Any
from ..transform.transform import TransformLike
from ._transformable import E, PointLike

__all__ = ["TransformMethods"]

class TransformMethods:
    t: Any

    def translate(
        self: E,
        dx: float,
        dy: float = 0.0,
        *,
        local: bool = False,
    ) -> E: ...
    def rotate(
        self: E,
        degrees: float,
        *,
        about: PointLike | None = None,
        local: bool = False,
    ) -> E: ...
    def scale(
        self: E,
        sx: float,
        sy: float | None = None,
        *,
        about: PointLike | None = None,
        local: bool = False,
    ) -> E: ...
    def skew(
        self: E,
        x_degrees: float = 0.0,
        y_degrees: float = 0.0,
        *,
        about: PointLike | None = None,
        local: bool = False,
    ) -> E: ...
    def flip_x(
        self: E,
        *,
        about: PointLike | None = None,
        local: bool = False,
    ) -> E: ...
    def flip_y(
        self: E,
        *,
        about: PointLike | None = None,
        local: bool = False,
    ) -> E: ...
    def apply(
        self: E,
        transform: TransformLike,
        *,
        local: bool = False,
    ) -> E: ...
    def reset(self: E) -> E: ...
    def __add__(self, other: Any) -> Any: ...
    def __radd__(self, other: Any) -> Any: ...
    def __iadd__(self, other: Any) -> Any: ...
    def __sub__(self, other: Any) -> Any: ...
    def __isub__(self, other: Any) -> Any: ...
    def __mul__(self: E, factor: float | tuple[float, float]) -> E: ...
    def __rmul__(self: E, factor: float) -> E: ...
    def __imul__(self: E, factor: float | tuple[float, float]) -> E: ...
    def __truediv__(self: E, divisor: float | tuple[float, float]) -> E: ...
    def __itruediv__(self: E, divisor: float | tuple[float, float]) -> E: ...
    def __matmul__(self: E, operand: TransformLike | float) -> E: ...
    def __imatmul__(self: E, operand: TransformLike | float) -> E: ...
    def __rmatmul__(self: E, transform: TransformLike) -> E: ...
