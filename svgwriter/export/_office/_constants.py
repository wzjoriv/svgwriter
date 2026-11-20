"""
Constants for the PowerPoint and Word exporters and readers.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "ALPHA_SCALE", "ASCENT", "A_NS", "BLANK_LAYOUT", "DEFAULT_TEXT_PT", "EMU_PER_POINT", "EMU_PER_UNIT",
    "EXTRA_HINT", "GENERIC_FONTS", "INLINE_GAP", "LINE_HEIGHT", "MARGIN", "PIC", "PICTURE_SCALE",
    "POINTS_PER_UNIT", "REL", "ROUND_RECT_ADJUST", "SLIDE_MAX_EMU", "SLIDE_MIN_EMU", "USER_UNITS_PER_INCH",
    "WP", "WPS"
]

EXTRA_HINT: Final = "pip install 'svgwriter[office]'"
PICTURE_SCALE: Final = 2.0
USER_UNITS_PER_INCH: Final = 96.0
WP: Final = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
WPS: Final = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
PIC: Final = "http://schemas.openxmlformats.org/drawingml/2006/picture"
REL: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
INLINE_GAP: Final = 10.0
MARGIN: Final = 10.0
EMU_PER_UNIT: Final = 9525
SLIDE_MIN_EMU: Final = 914400
SLIDE_MAX_EMU: Final = 51206400
BLANK_LAYOUT: Final = 6
ALPHA_SCALE: Final = 100000
POINTS_PER_UNIT: Final = 0.75
DEFAULT_TEXT_PT: Final = 18.0
ROUND_RECT_ADJUST: Final = 16667
EMU_PER_POINT: Final = 12700
LINE_HEIGHT: Final = 1.2
ASCENT: Final = 0.9
GENERIC_FONTS: Final = {"sans-serif": "Arial", "serif": "Times New Roman", "monospace": "Courier New",
                        "system-ui": "Segoe UI", "cursive": "Comic Sans MS"}
A_NS: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
