from collections.abc import Mapping
from typing import Any, ClassVar, TypeAlias, TypeVar
from ..pathdata.data import BBox
from ..transform.matrix import Matrix, Point
from ..transform.transform import TransformLike
from ._moves import TransformMethods
from ._placement import Placement
from .base import AttrValue, Child, Element

__all__ = ["PointLike", "Transformable", "children_bbox", "offset"]

PointLike: TypeAlias = tuple[float, float] | Point
E = TypeVar('E', bound='Transformable')

def offset(value: object) -> tuple[float, float] | None: ...

def children_bbox(element: Element) -> BBox | None: ...

class Transformable(Placement, TransformMethods, Element):
    transform_attribute: ClassVar[str]
    anchor: PointLike | None

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
