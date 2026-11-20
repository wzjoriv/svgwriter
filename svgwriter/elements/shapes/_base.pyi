from abc import ABC, abstractmethod
from ...pathdata.data import BBox
from .._behavior._geometry import PathOperand
from .._behavior._mixins import GraphicsElement
from .._behavior._viewport import user_units as user_units
from ..core._element import Category

__all__ = ["Shape", "parse_points", "user_units"]

def parse_points(text: str) -> list[tuple[float, float]]: ...

class Shape(PathOperand, GraphicsElement, ABC, category=Category.SHAPE):
    @property
    @abstractmethod
    def bbox(self) -> BBox: ...
    def local_bbox(self) -> BBox: ...
