from typing import Literal
from ...document import Document

__all__ = ["to_dxf", "to_gcode", "to_hpgl"]

def to_dxf(
    document: Document,
    *,
    tolerance: float = 0.05,
    unit_mm: float = 0.26458333333333334,
) -> str: ...

def to_hpgl(
    document: Document,
    *,
    tolerance: float = 0.05,
    unit_mm: float = 0.26458333333333334,
) -> str: ...

def to_gcode(
    document: Document,
    *,
    tolerance: float = 0.05,
    unit_mm: float = 0.26458333333333334,
    feed: float = 1000.0,
    travel_z: float = 2.0,
    cut_z: float = -0.5,
    mode: Literal['mill', 'laser'] = 'mill',
    power: float = 1000.0,
) -> str: ...
