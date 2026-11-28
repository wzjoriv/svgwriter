"""
Constants for ``svgwriter.library.patterns``: default spacings, sizes and sampling.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "DEFAULT_ANGLE",
    "DEFAULT_GAP",
    "DOT_RADIUS",
    "FALLBACK_INK",
    "LINE_WIDTH",
    "NOISE_CELL",
    "NOISE_DENSITY",
    "NOISE_FAINTEST",
    "NOISE_TILE",
    "ROLE",
    "WAVE_AMPLITUDE",
    "WAVE_LENGTH",
    "WAVE_SAMPLES",
]

ROLE: Final = "pattern"
FALLBACK_INK: Final = "black"
DEFAULT_ANGLE: Final = 45.0
DEFAULT_GAP: Final = 6.0
LINE_WIDTH: Final = 1.0
DOT_RADIUS: Final = 1.5
WAVE_LENGTH: Final = 16.0
WAVE_AMPLITUDE: Final = 3.0
WAVE_SAMPLES: Final = 24
NOISE_TILE: Final = 32
NOISE_CELL: Final = 2.0
NOISE_DENSITY: Final = 0.5
NOISE_FAINTEST: Final = 0.2
