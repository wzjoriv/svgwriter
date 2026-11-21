"""
Constants for ``svgwriter.text_effects``: palettes, strengths and animation timings.

Lengths and noise frequencies are tuned for glyphs ``REFERENCE_HEIGHT`` units tall and scale with the text.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "FIRE_COLORS",
    "FIRE_DURATION",
    "FIRE_FREQUENCIES",
    "FIRE_GLOW",
    "FIRE_HEAT",
    "GLITCH_COLORS",
    "GLITCH_DURATION",
    "GLITCH_SHIFTS",
    "ICE_COLORS",
    "ICE_DURATION",
    "ICE_FROST",
    "ICE_GLINT",
    "ICE_SWEEP",
    "LIGHT_ELEVATION",
    "METAL_DURATION",
    "METAL_EDGE",
    "METAL_LIGHT",
    "METAL_ROUNDING",
    "METAL_SHADOW",
    "METAL_SWEEP",
    "NEON_DURATION",
    "NEON_FLICKER",
    "NEON_GLOWS",
    "NEON_STROKE",
    "NEON_TUBE",
    "REFERENCE_HEIGHT",
    "REGION_EXTENT",
    "REGION_MARGIN",
    "REGION_PAD",
    "SMOKE_COLOR",
    "SMOKE_DURATION",
    "SMOKE_FREQUENCIES",
    "SMOKE_HAZE",
    "SMOKE_SCALES",
    "SMOKE_SOFTEN",
    "SNOW_COLORS",
    "SNOW_DENSITY",
    "SNOW_DURATION",
    "SNOW_FALL",
    "SNOW_FLAKES",
    "SNOW_GLOW",
    "SNOW_RIM",
    "WIND_COLORS",
    "WIND_DURATION",
    "WIND_GUSTS",
    "WIND_STREAK",
]

REFERENCE_HEIGHT: Final = 32.0
REGION_PAD: Final = 0.9
REGION_MARGIN: Final = "-60%"
REGION_EXTENT: Final = "220%"
LIGHT_ELEVATION: Final = 35.0

FIRE_COLORS: Final = ("#fff3b0", "#ffb703", "#fb5607", "#c1121f", "#6a040f")
FIRE_FREQUENCIES: Final = ((0.025, 0.07), (0.03, 0.1), (0.022, 0.085), (0.025, 0.07))
FIRE_HEAT: Final = 5.0
FIRE_GLOW: Final = ("#ff7b00", 4.0)
FIRE_DURATION: Final = 1.2

ICE_COLORS: Final = ("#ffffff", "#caf0f8", "#90e0ef", "#0096c7", "#023e8a")
ICE_FROST: Final = ("#bde0fe", 2.5)
ICE_GLINT: Final = (1.5, 0.7, 24.0)
ICE_SWEEP: Final = (150.0, 330.0, 150.0)
ICE_DURATION: Final = 3.0

SMOKE_COLOR: Final = "#8d939b"
SMOKE_FREQUENCIES: Final = ((0.012, 0.05), (0.018, 0.07), (0.012, 0.05))
SMOKE_SCALES: Final = (5.0, 9.0, 5.0)
SMOKE_SOFTEN: Final = 0.6
SMOKE_HAZE: Final = (5.0, 0.45)
SMOKE_DURATION: Final = 4.0

METAL_EDGE: Final = ("#2f3338", 0.6)
METAL_LIGHT: Final = (40.0, 0.8, 18.0, 2.5)
METAL_ROUNDING: Final = 1.0
METAL_SHADOW: Final = (1.0, 0.4)
METAL_SWEEP: Final = (200.0, 250.0, 200.0)
METAL_DURATION: Final = 3.0

WIND_COLORS: Final = ("#e0fbfc", "#98c1d9", "#5c8fb0")
WIND_STREAK: Final = (8.0, 10.0, 0.55)
WIND_GUSTS: Final = (-6.0, -16.0, -6.0)
WIND_DURATION: Final = 1.6

SNOW_COLORS: Final = ("#ffffff", "#e8f1fb", "#bcd4ea")
SNOW_RIM: Final = 1.0
SNOW_FLAKES: Final = (0.18, 14.0)
SNOW_DENSITY: Final = -10.0
SNOW_GLOW: Final = (1.5, 0.6)
SNOW_FALL: Final = 60.0
SNOW_DURATION: Final = 3.0

NEON_TUBE: Final = 0.75
NEON_STROKE: Final = 1.0
NEON_GLOWS: Final = (2.0, 6.0, 12.0)
NEON_FLICKER: Final = ("1", "1", "0.55", "1", "0.8", "1", "1")
NEON_DURATION: Final = 2.5

GLITCH_COLORS: Final = ("#ff004d", "#00e5ff")
GLITCH_SHIFTS: Final = (2.0, -3.0, 4.0, 0.0, -2.0, 3.0, 1.0)
GLITCH_DURATION: Final = 1.4
