from typing import Any, ClassVar, TypeAlias
from ...pathdata.data import PathData
from ...transform.transform import TransformLike
from ..core import Element
from ..shapes import Path
from ._boolean import BooleanOps
from ._measure import Measurement

__all__ = ["Operand", "PathOperand"]

Operand: TypeAlias = PathOperand | PathData | str

class PathOperand(BooleanOps, Measurement, Element):
    geometry_attributes: ClassVar[frozenset[str]]

    def local_outline(self) -> PathData: ...
    def outline(self) -> PathData: ...
    def to_path(self, **kwargs: Any) -> Path: ...
    def flatten_clip(self) -> Path: ...
    def expand_pattern(self) -> Element: ...
    def transformed(self, transform: TransformLike) -> Path: ...
