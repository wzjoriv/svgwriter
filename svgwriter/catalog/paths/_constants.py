"""
Constants for ``svgwriter.catalog.paths``: defaults, tables and patterns.
"""

from __future__ import annotations

import math
from typing import Final

__all__ = [
    "ARROW_HEAD_ANGLE",
    "CALLOUT_RADIUS",
    "CALLOUT_TAIL_RATIO",
    "CROSS_THICKNESS_RATIO",
    "DASH_PATTERN",
    "DEFAULT_HEAD_SIZE",
    "DEFAULT_INNER_RATIO",
    "DEFAULT_STAR_POINTS",
    "DEFAULT_TEETH",
    "DOT_RADIUS",
    "FALLBACK_INK",
    "FULL_TURN",
    "HEART_CURVES",
    "HEART_MIDLINE",
    "HEART_NOTCH",
    "MIN_SIDES",
    "QUARTER_TURN",
    "ROUNDING_EPSILON",
    "SINE_CONTROL_X",
    "SINE_CONTROL_Y",
    "SPIRAL_SEGMENTS_PER_TURN",
    "TOOTH_DEPTH_RATIO",
    "WAVE_CYCLES",
    "WAVE_KINDS",
]

MIN_SIDES: Final = 3

DASH_PATTERN: Final = (4, 2)
DOT_RADIUS: Final = 2
FALLBACK_INK: Final = "black"

FULL_TURN: Final = 360.0

QUARTER_TURN: Final = 90.0
DEFAULT_STAR_POINTS: Final = 5
DEFAULT_INNER_RATIO: Final = 0.5
DEFAULT_HEAD_SIZE: Final = 10.0
ARROW_HEAD_ANGLE: Final = 30.0
DEFAULT_TEETH: Final = 12
TOOTH_DEPTH_RATIO: Final = 0.15

CALLOUT_RADIUS: Final = 8.0
CALLOUT_TAIL_RATIO: Final = 0.3
CROSS_THICKNESS_RATIO: Final = 1 / 3
ROUNDING_EPSILON: Final = 1e-9
SPIRAL_SEGMENTS_PER_TURN: Final = 4

HEART_NOTCH: Final = (0.0, -0.22)
HEART_CURVES: Final = (
    ((-0.03, -0.38), (-0.12, -0.45), (-0.25, -0.45)),
    ((-0.39, -0.45), (-0.5, -0.33), (-0.5, -0.2)),
    ((-0.5, 0.08), (-0.2, 0.28), (0.0, 0.5)),
)
HEART_MIDLINE: Final = 0.025

SINE_CONTROL_X: Final = 4 / (3 * math.pi)
SINE_CONTROL_Y: Final = 4 / 3

WAVE_KINDS: Final = {
    "triangle": ((0.0, 0.0), (0.25, 1.0), (0.75, -1.0)),
    "square": ((0.0, 1.0), (0.5, 1.0), (0.5, -1.0), (1.0, -1.0)),
    "sawtooth": ((0.0, -1.0), (1.0, 1.0)),
}
WAVE_CYCLES: Final = ("sine", *WAVE_KINDS)
