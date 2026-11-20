from typing import Literal, TypeAlias
from ..pathdata.data import BBox, PathData
from ..transform.matrix import Point
from ._skia import Geometry

__all__ = [
    "Cap",
    "Join",
    "bounds",
    "contains",
    "point_at_length",
    "stroke_to_path",
    "tangent_at_length",
    "total_length",
]

Cap: TypeAlias = Literal['butt', 'round', 'square']
Join: TypeAlias = Literal['miter', 'round', 'bevel']

def bounds(item: Geometry) -> BBox: ...

def contains(
    item: Geometry,
    x: float,
    y: float,
) -> bool: ...

def total_length(item: Geometry) -> float: ...

def point_at_length(item: Geometry, distance: float) -> Point: ...

def tangent_at_length(item: Geometry, distance: float) -> Point: ...

def stroke_to_path(
    item: Geometry,
    width: float = 1.0,
    *,
    cap: Cap = 'butt',
    join: Join = 'miter',
    miter_limit: float = 4.0,
) -> PathData: ...
