"""
Constants of lengths, angles and quantities: unit spellings, scales and parsing patterns.
"""

from __future__ import annotations

import math
import re
from typing import Final

__all__ = [
    "ANGLE_RE",
    "ANGLE_SPELLINGS",
    "DEGREES_PER",
    "EQUAL_DIGITS",
    "FULL_TURN_DEGREES",
    "HALF_TURN_DEGREES",
    "LENGTH_RE",
    "LENGTH_SCALES",
    "LENGTH_SPELLINGS",
    "SUPERSCRIPTS",
]

EQUAL_DIGITS: Final = 9
"""Decimal places at which lengths, angles and quantities in different units count as equal."""
FULL_TURN_DEGREES: Final = 360.0
HALF_TURN_DEGREES: Final = FULL_TURN_DEGREES / 2
DEGREES_PER: Final = {"deg": 1.0, "rad": 180.0 / math.pi, "grad": 0.9, "turn": FULL_TURN_DEGREES}
ANGLE_RE: Final = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*([A-Za-z]+)?\s*$")
ANGLE_SPELLINGS: Final = {
    **{unit: unit for unit in DEGREES_PER},
    "degree": "deg", "degrees": "deg", "radian": "rad", "radians": "rad",
    "gon": "grad", "gradian": "grad", "gradians": "grad", "turns": "turn",
}
LENGTH_SPELLINGS: Final = {
    "": "", "px": "px", "pt": "pt", "pc": "pc", "mm": "mm", "cm": "cm", "in": "in",
    "em": "em", "ex": "ex", "%": "%", "q": "Q", "m": "m", "ft": "ft",
    "pixel": "px", "pixels": "px", "point": "pt", "points": "pt", "inch": "in", "inches": "in",
    "millimeter": "mm", "millimeters": "mm", "millimetre": "mm", "millimetres": "mm",
    "centimeter": "cm", "centimeters": "cm", "centimetre": "cm", "centimetres": "cm",
    "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "km": "km", "kilometer": "km", "kilometers": "km", "kilometre": "km", "kilometres": "km",
    "um": "um", "µm": "um", "micrometer": "um", "micrometers": "um", "micrometre": "um", "micrometres": "um",
    "micron": "um", "microns": "um", "foot": "ft", "feet": "ft", "yd": "yd", "yard": "yd", "yards": "yd",
    "mi": "mi", "mile": "mi", "miles": "mi", "furlong": "furlong", "furlongs": "furlong",
    "mil": "mil", "mils": "mil", "thou": "mil", "nmi": "nmi", "nautical mile": "nmi", "nautical miles": "nmi",
    "pica": "pc", "picas": "pc", "quarter millimeter": "Q", "quarter millimetre": "Q",
}
LENGTH_SCALES: Final = {
    "m": ("mm", 1000.0), "km": ("mm", 1_000_000.0), "um": ("mm", 0.001), "nmi": ("mm", 1_852_000.0),
    "ft": ("in", 12.0), "yd": ("in", 36.0), "mi": ("in", 63_360.0), "furlong": ("in", 7920.0), "mil": ("in", 0.001),
}
"""Units SVG has no suffix for, as (SVG suffix, how many of it make one)."""
SUPERSCRIPTS: Final = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
LENGTH_RE: Final = re.compile(
    r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*([A-Za-z]+|%)?\s*$"
)
