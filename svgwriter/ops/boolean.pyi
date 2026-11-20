from enum import Enum
from ..pathdata.data import PathData
from ._skia import Geometry

__all__ = ["BooleanOp", "combine", "difference", "intersection", "simplify", "union", "xor"]

class BooleanOp(Enum):
    UNION = 'kUnion_PathOp'
    INTERSECTION = 'kIntersect_PathOp'
    DIFFERENCE = 'kDifference_PathOp'
    REVERSE_DIFFERENCE = 'kReverseDifference_PathOp'
    XOR = 'kXOR_PathOp'

def combine(
    first: Geometry,
    second: Geometry,
    op: BooleanOp,
) -> PathData: ...

def union(first: Geometry, *others: Geometry) -> PathData: ...

def intersection(first: Geometry, second: Geometry) -> PathData: ...

def difference(first: Geometry, second: Geometry) -> PathData: ...

def xor(first: Geometry, second: Geometry) -> PathData: ...

def simplify(item: Geometry) -> PathData: ...
