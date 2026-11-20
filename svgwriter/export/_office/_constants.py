"""
Constants for the PowerPoint and Word exporters and readers.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "A14_NS", "ALPHA_SCALE", "ANGLE_UNIT", "ASCENT", "A_NS", "BAR_CHARS", "BLANK_LAYOUT", "CAPS",
    "DEFAULT_TEXT_PT", "EMU_PER_POINT", "EMU_PER_UNIT", "EQUATION_ID", "EXTRA_HINT", "GENERIC_FONTS",
    "GROUP_CHARS", "HALF_POINTS_PER_UNIT", "INLINE_GAP", "JOINS", "LINE_HEIGHT", "MARGIN", "MATHML_NS",
    "MATH_FONT", "MC_NS", "MITER_SCALE", "M_NS", "NARY_CHARS", "PIC", "PICTURE_SCALE", "POINTS_PER_UNIT", "REL",
    "ROUND_RECT_ADJUST", "SLIDE_MAX_EMU", "SLIDE_MIN_EMU", "USER_UNITS_PER_INCH", "WP", "WPS", "W_NS"
]

EXTRA_HINT: Final = "pip install 'pysvgwriter[office]'"
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
M_NS: Final = "http://schemas.openxmlformats.org/officeDocument/2006/math"
MATHML_NS: Final = "http://www.w3.org/1998/Math/MathML"
A14_NS: Final = "http://schemas.microsoft.com/office/drawing/2010/main"
MC_NS: Final = "http://schemas.openxmlformats.org/markup-compatibility/2006"
W_NS: Final = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MATH_FONT: Final = "Cambria Math"
HALF_POINTS_PER_UNIT: Final = 1.5
EQUATION_ID: Final = 1000
NARY_CHARS: Final = frozenset("∑∏∐∫∬∭∮∯∰⋃⋂⋁⋀"
                              "⨀⨁⨂⨄⨆")
BAR_CHARS: Final = frozenset("―¯‾_̲")
GROUP_CHARS: Final = frozenset("⏞⏟")
ANGLE_UNIT: Final = 60000
MITER_SCALE: Final = 100000
CAPS: Final = {"butt": "flat", "round": "rnd", "square": "sq"}
JOINS: Final = {"miter": "miter", "round": "round", "bevel": "bevel"}
