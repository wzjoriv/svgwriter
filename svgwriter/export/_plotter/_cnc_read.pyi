from ...document import Document

__all__ = ["read_dxf", "read_gcode", "read_hpgl"]

def read_dxf(
    text: str,
    *,
    unit_mm: float = 0.26458333333333334,
) -> Document: ...

def read_hpgl(
    text: str,
    *,
    unit_mm: float = 0.26458333333333334,
) -> Document: ...

def read_gcode(
    text: str,
    *,
    unit_mm: float = 0.26458333333333334,
) -> Document: ...
