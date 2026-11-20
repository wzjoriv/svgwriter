from typing import Literal
from ...document import Document as Document
from .._registry import register as register, register_importer as register_importer

def dxf(
    document: Document,
    *,
    tolerance: float = 0.05,
    unit_mm: float = 0.26458333333333334,
) -> str: ...

def hpgl(
    document: Document,
    *,
    tolerance: float = 0.05,
    unit_mm: float = 0.26458333333333334,
) -> str: ...

def gcode(
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

def read_dxf(
    data: bytes,
    *,
    unit_mm: float = 0.26458333333333334,
) -> Document: ...

def read_hpgl(
    data: bytes,
    *,
    unit_mm: float = 0.26458333333333334,
) -> Document: ...

def read_gcode(
    data: bytes,
    *,
    unit_mm: float = 0.26458333333333334,
) -> Document: ...
