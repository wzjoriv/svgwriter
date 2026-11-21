"""
Constants for ``svgwriter.gradients``: sampling, palettes and finishes.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "IRIDESCENT_CHROMA",
    "IRIDESCENT_LIGHTNESS",
    "IRIDESCENT_STEPS",
    "METAL_BANDS",
    "MESH_CORNERS",
    "MESH_REACH",
    "OCEAN",
    "SAMPLES",
    "SPACE",
    "SUNSET",
]

SPACE: Final = "oklch"
SAMPLES: Final = 4
SUNSET: Final = ("#2b1055", "#d53369", "#ff7e5f", "#feb47b", "#ffe29f")
OCEAN: Final = ("#e0f7fa", "#4dd0e1", "#0288d1", "#01579b", "#0a1931")
METAL_BANDS: Final = ((0.0, 0.35), (0.22, -0.25), (0.45, 0.45), (0.5, -0.1), (0.72, 0.2), (1.0, -0.35))
IRIDESCENT_LIGHTNESS: Final = 0.82
IRIDESCENT_CHROMA: Final = 0.12
MESH_REACH: Final = 0.9
IRIDESCENT_STEPS: Final = 6
MESH_CORNERS: Final = ((0, 0), (1, 0), (1, 1), (0, 1))
