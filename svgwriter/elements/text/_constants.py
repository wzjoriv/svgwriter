"""
Constants for the text elements: font defaults, whitespace handling and grapheme clusters.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "DEFAULT_FONT_FAMILY",
    "DEFAULT_FONT_SIZE",
    "JOINING_RANGES",
    "PERCENT",
    "POSITION_NAMES",
    "REGIONAL_INDICATORS",
    "WHITESPACE_DEFAULT",
    "WHITESPACE_PRESERVE",
    "ZWJ",
]

PERCENT: Final = 100.0
POSITION_NAMES: Final = ("x", "y", "dx", "dy", "rotate")
DEFAULT_FONT_FAMILY: Final = "sans-serif"
DEFAULT_FONT_SIZE: Final = 16.0
WHITESPACE_PRESERVE: Final = {10: " ", 13: " ", 9: " "}
WHITESPACE_DEFAULT: Final = {10: None, 13: None, 9: " "}
ZWJ: Final = "‍"
JOINING_RANGES: Final = (
    (0xFE00, 0xFE0F), (0xE0100, 0xE01EF),  # variation selectors
    (0x1F3FB, 0x1F3FF),  # emoji skin tones
    (0xE0020, 0xE007F),  # emoji tag sequences
    (0x20E3, 0x20E3),  # combining keycap
)
REGIONAL_INDICATORS: Final = (0x1F1E6, 0x1F1FF)
