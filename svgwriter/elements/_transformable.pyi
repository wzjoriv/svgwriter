from collections.abc import Mapping
from typing import Any, ClassVar, TypeAlias, TypeVar
from ..pathdata.data import BBox
from ..transform.matrix import Matrix, Point
from ..transform.transform import TransformLike
from .base import AttrValue, Child, Element

__all__ = ["PointLike", "Transformable", "children_bbox", "offset"]

PointLike: TypeAlias = tuple[float, float] | Point
E = TypeVar('E', bound='Transformable')

def offset(value: object) -> tuple[float, float] | None: ...

def children_bbox(element: Element) -> BBox | None: ...

class Transformable(Element):
    transform_attribute: ClassVar[str]

    def __init__(
        self,
        *args: Child,
        t: TransformLike | None = None,
        transform: TransformLike | None = None,
        anchor: PointLike | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @property
    def t(self) -> Matrix: ...
    @t.setter
    def t(self, value: TransformLike | None) -> None: ...
    @property
    def transform(self) -> Matrix: ...
    @transform.setter
    def transform(self, value: TransformLike | None) -> None: ...
    def local_bbox(self) -> BBox | None: ...
    @property
    def anchor(self) -> Point: ...
    @anchor.setter
    def anchor(self, value: PointLike | None) -> None: ...
    @property
    def position(self) -> Point: ...
    @position.setter
    def position(self, value: PointLike) -> None: ...
    def place(
        self: E,
        x: float,
        y: float,
        *,
        at: str | None = None,
    ) -> E: ...
    def align(
        self: E,
        target: Any,
        at: str = 'center',
        *,
        to: str | None = None,
        offset: PointLike = (0.0, 0.0),
    ) -> E: ...
    def bounds(self) -> BBox | None: ...
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
