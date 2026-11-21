"""
Constants for the DXF, HPGL and G-code exporters and readers.
"""

from __future__ import annotations

import re
from typing import Final

from ...._internal._constants import MM_PER_INCH, PX_PER_INCH

__all__ = [
    "ARC_STEP_DEGREES",
    "DEFAULT_TOLERANCE",
    "DXF_POINT_FIELDS",
    "DXF_VARIABLE",
    "DXF_X",
    "DXF_Y",
    "GCODE_PAGE_RE",
    "GCODE_WORD_RE",
    "HEX_RE",
    "HPGL_PENS",
    "HPGL_RE",
    "HPGL_UNITS_PER_MM",
    "MAX_PAGE_MM",
    "MM_PER_USER_UNIT",
    "PRECISION",
]

MM_PER_USER_UNIT: Final = MM_PER_INCH / PX_PER_INCH
DEFAULT_TOLERANCE: Final = 0.05
HPGL_UNITS_PER_MM: Final = 40.0
PRECISION: Final = 4
HPGL_PENS: Final = {0: "none", 1: "black", 2: "red", 3: "green", 4: "yellow", 5: "blue", 6: "magenta", 7: "cyan"}
ARC_STEP_DEGREES: Final = 5.0
HEX_RE: Final = re.compile(r"^[0-9A-Fa-f]{6}$")
HPGL_RE: Final = re.compile(r"([A-Z]{2})([^;A-Z]*)")
DXF_VARIABLE: Final = 9
DXF_X: Final = 10
DXF_Y: Final = 20
DXF_POINT_FIELDS: Final = 4
MAX_PAGE_MM: Final = 1e7
GCODE_PAGE_RE: Final = re.compile(r"\(page ([\d.]+) x ([\d.]+) mm\)")
GCODE_WORD_RE: Final = re.compile(r"([A-Z])\s*([-+]?\d*\.?\d+)")
