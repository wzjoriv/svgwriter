"""
Constants for ``svgwriter.model.pathdata``: defaults, tables and patterns.
"""

from __future__ import annotations

import math
import re
from typing import Final

__all__ = [
    "ARC_FLAG_POSITIONS",
    "ARC_SAMPLES",
    "ARITY",
    "BOX_POINTS",
    "CURVE_SAMPLES",
    "FULL_CIRCLE",
    "FULL_TURN",
    "IMPLIED",
    "NUMBER_RE",
    "QUARTER_TURN",
    "SEPARATORS",
]

FULL_TURN: Final = 2.0 * math.pi

FULL_CIRCLE: Final = 360.0
QUARTER_TURN: Final = 90.0

CURVE_SAMPLES: Final = 16
ARC_SAMPLES: Final = 32
IMPLIED: Final = {"M": "L", "m": "l"}
BOX_POINTS: Final[dict[str, tuple[float, float]]] = {
    "center": (0.5, 0.5),
    "top_left": (0.0, 0.0), "top_center": (0.5, 0.0), "top_right": (1.0, 0.0),
    "center_left": (0.0, 0.5), "center_right": (1.0, 0.5),
    "bottom_left": (0.0, 1.0), "bottom_center": (0.5, 1.0), "bottom_right": (1.0, 1.0),
    "top": (0.5, 0.0), "bottom": (0.5, 1.0), "left": (0.0, 0.5), "right": (1.0, 0.5),
}
"""Named points of a box as fractions of its width and height, from the top-left corner."""

NUMBER_RE: Final = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
SEPARATORS: Final = " \t\r\n,"
ARITY: Final = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}
ARC_FLAG_POSITIONS: Final = (3, 4)
