"""
Constants for ``svgwriter.filters``: regions, defaults, roles and kernels.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "ALPHA_ROW",
    "DEFAULT_BLUR",
    "DEFAULT_OFFSET",
    "EMBOSS_KERNEL",
    "FALLBACK_INK",
    "FALLBACK_SHADOW",
    "FILTER_EXTENT",
    "FILTER_MARGIN",
    "GOO_BLUR",
    "GOO_CONTRAST",
    "GOO_CUTOFF",
    "GRAIN_AMOUNT",
    "GRAIN_FREQUENCY",
    "INK_ROLE",
    "LIGHT_AZIMUTH",
    "LIGHT_ELEVATION",
    "LONG_SHADOW_EXTENT",
    "LONG_SHADOW_LENGTH",
    "LUMA",
    "OUTLINE_WIDTH",
    "SHADOW_ROLE",
    "SPECULAR_CONSTANT",
    "SPECULAR_EXPONENT",
    "SRGB",
    "SURFACE_SCALE",
    "WIDE_EXTENT",
    "WIDE_MARGIN",
]

FILTER_MARGIN: Final = "-20%"
FILTER_EXTENT: Final = "140%"
WIDE_MARGIN: Final = "-50%"
WIDE_EXTENT: Final = "200%"
LONG_SHADOW_EXTENT: Final = "400%"
SRGB: Final = "sRGB"

DEFAULT_BLUR: Final = 2.0
DEFAULT_OFFSET: Final = 2.0
SHADOW_ROLE: Final = "filter.shadow"
INK_ROLE: Final = "filter.ink"
FALLBACK_SHADOW: Final = "rgba(0,0,0,0.35)"
FALLBACK_INK: Final = "black"

LONG_SHADOW_LENGTH: Final = 24.0
OUTLINE_WIDTH: Final = 2.0

EMBOSS_KERNEL: Final = (-2.0, -1.0, 0.0, -1.0, 1.0, 1.0, 0.0, 1.0, 2.0)

GOO_BLUR: Final = 8.0
GOO_CONTRAST: Final = 20.0
GOO_CUTOFF: Final = -7.0

GRAIN_AMOUNT: Final = 0.25
GRAIN_FREQUENCY: Final = 0.8

LUMA: Final = (0.2126, 0.7152, 0.0722)
ALPHA_ROW: Final = (0.0, 0.0, 0.0, 1.0, 0.0)

LIGHT_AZIMUTH: Final = 225.0
LIGHT_ELEVATION: Final = 45.0
SURFACE_SCALE: Final = 3.0
SPECULAR_EXPONENT: Final = 20.0
SPECULAR_CONSTANT: Final = 0.6
