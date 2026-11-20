from typing import Any, TypeAlias
from ..elements._geometry import PathOperand
from ..pathdata.data import PathData

__all__ = ["Geometry", "from_skia", "geometry_data", "to_skia"]

Geometry: TypeAlias = PathOperand | PathData | str

def geometry_data(item: Geometry) -> tuple[PathData, bool]: ...

def to_skia(
    data: PathData,
    *,
    evenodd: bool = False,
) -> Any: ...

def from_skia(path: Any) -> PathData: ...
