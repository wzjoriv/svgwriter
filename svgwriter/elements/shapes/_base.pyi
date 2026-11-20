from abc import ABC, abstractmethod
from ...pathdata.data import BBox
from .._geometry import PathOperand
from .._mixins import GraphicsElement
from .._viewport import user_units as user_units
from ..base import Category

__all__ = ["Shape", "parse_points", "user_units"]

def parse_points(text: str) -> list[tuple[float, float]]: ...

class Shape(PathOperand, GraphicsElement, ABC, category=Category.SHAPE):
    @property
    @abstractmethod
    def bbox(self) -> BBox: ...
    def local_bbox(self) -> BBox: ...
