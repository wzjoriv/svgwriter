"""
Named constants for the built-in interpolators.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "DISCRETE_SWITCH",
    "FULL_TURN",
    "GEOMETRY_SKIP",
    "HALF_TURN",
    "MORPH_CORNER",
    "MORPH_FLATNESS",
    "MORPH_MAX_POINTS",
    "MORPH_MIN_POINTS",
    "MORPH_SPACING",
]

HALF_TURN: Final = 180.0
FULL_TURN: Final = 360.0
DISCRETE_SWITCH: Final = 0.5
GEOMETRY_SKIP: Final = frozenset({"id", "transform", "d", "points"})
MORPH_SPACING: Final = 0.012
MORPH_FLATNESS: Final = 0.001
MORPH_CORNER: Final = 0.35
MORPH_MAX_POINTS: Final = 600
MORPH_MIN_POINTS: Final = 24
