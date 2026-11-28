"""
Constants for the PowerPoint and Word exporters and readers.
"""

from __future__ import annotations

import re
from typing import Final

from ...._internal._constants import PT_PER_INCH, PX_PER_INCH, PX_PER_PT

__all__ = [
    "ACCEL_SCALE", "SCHEME_ALIASES", "STYLE_LINE_WIDTH", "THEME_RELATIONSHIP", "HORIZONTAL_ALIGNS", "VERTICAL_ANCHORS", "STAR_INNER_RATIO", "ANIMATION_KEY", "CLICK_EVENTS", "CLICK_START_RE", "TRIGGER_KEY", "A14_NS", "COLOR_ATTRIBUTES", "EFFECT_PRESETS", "MS_PER_SECOND", "P_NS",
    "PATH_TOLERANCE", "PERCENT_SCALE", "REPEAT_SCALE", "ALPHA_SCALE", "ANGLE_UNIT", "ASCENT", "A_NS", "BAR_CHARS", "BLANK_LAYOUT", "CAPS",
    "DEFAULT_TEXT_PT", "EMU_PER_INCH", "EMU_PER_POINT", "EMU_PER_UNIT", "EQUATION_ID", "GENERIC_FONTS",
    "GROUP_CHARS", "HALF_POINTS_PER_UNIT", "HEADING_STYLE_RE", "HEX_COLOR_RE", "INLINE_GAP", "JOINS", "LINE_HEIGHT", "LIST_STYLE", "MARGIN", "MATHML_NS",
    "MATH_FONT", "MC_NS", "MITER_SCALE", "M_NS", "NARY_CHARS", "NUMBERED_STYLE", "OFF_VALUES", "PIC", "PICTURE_SCALE", "POINTS_PER_UNIT",
    "PPTX_SIZE_SCALE", "REL",
    "ROUND_RECT_ADJUST", "SLIDE_MAX_EMU", "SLIDE_MIN_EMU", "TITLE_STYLE", "TWIPS_PER_UNIT", "WP", "WPS", "W_NS"
]

PICTURE_SCALE: Final = 2.0
WP: Final = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
WPS: Final = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
PIC: Final = "http://schemas.openxmlformats.org/drawingml/2006/picture"
REL: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
INLINE_GAP: Final = 10.0
MARGIN: Final = 10.0
EMU_PER_INCH: Final = 914400
EMU_PER_UNIT: Final = round(EMU_PER_INCH / PX_PER_INCH)
SLIDE_MIN_EMU: Final = EMU_PER_INCH
SLIDE_MAX_EMU: Final = 51206400
BLANK_LAYOUT: Final = 6
ALPHA_SCALE: Final = 100000
POINTS_PER_UNIT: Final = 1 / PX_PER_PT
PPTX_SIZE_SCALE: Final = 100
DEFAULT_TEXT_PT: Final = 18.0
ROUND_RECT_ADJUST: Final = 16667
EMU_PER_POINT: Final = round(EMU_PER_INCH / PT_PER_INCH)
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
HEADING_STYLE_RE: Final = re.compile(r"^Heading(\d)$")
TITLE_STYLE: Final = "Title"
NUMBERED_STYLE: Final = "ListNumber"
OFF_VALUES: Final = frozenset({"0", "false", "none", "off"})
HEX_COLOR_RE: Final = re.compile(r"[0-9A-Fa-f]{6}")
TWIPS_PER_UNIT: Final = 15
LIST_STYLE: Final = "List"
P_NS: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
ANIMATION_KEY: Final = "data-svgwriter-animation"
"""Attribute tying animated elements of an export copy to the shapes drawn from them."""
TRIGGER_KEY: Final = "data-svgwriter-trigger"
"""Attribute marking elements whose click starts animations, tying them to the shapes drawn from them."""
CLICK_EVENTS: Final = frozenset({"click", "mousedown", "mouseup"})
"""SMIL events PowerPoint plays as a click trigger on the shape (it has no hover trigger)."""
CLICK_START_RE: Final = re.compile(r"^\s*([^\s.;]+)\.(\w+)\s*(?:\+\s*([^;]+))?$")
"""An event ``begin`` such as ``key.click+0.5s``: the element id, the event and the delay."""
MS_PER_SECOND: Final = 1000
REPEAT_SCALE: Final = 1000
"""PowerPoint ``repeatCount`` is in thousandths."""
ACCEL_SCALE: Final = 100000
"""PowerPoint ``accel`` and ``decel`` are in thousandths of a percent."""
PERCENT_SCALE: Final = 100000
"""PowerPoint scale factors are in thousandths of a percent."""
PATH_TOLERANCE: Final = 0.5
"""Largest gap, in page units, between a motion path's curve and the polyline written for it."""
EFFECT_PRESETS: Final = {
    "appear": ("entr", 1), "fade_in": ("entr", 10), "disappear": ("exit", 1), "fade_out": ("exit", 10),
    "scale": ("emph", 6), "rotate": ("emph", 8), "color": ("emph", 1), "motion": ("path", 0),
}
"""PowerPoint ``presetClass`` and ``presetID`` per effect kind (Appear, Fade, Grow/Shrink, Spin, Change Fill Color, Custom Path)."""
COLOR_ATTRIBUTES: Final = {"fill": "fillcolor", "stroke": "stroke.color"}
"""SVG paint attributes and the PowerPoint shape properties a colour effect animates."""
STAR_INNER_RATIO: Final = 0.382
"""Inner radius of a five-point star preset as a share of its outer radius."""
HORIZONTAL_ALIGNS: Final = {"l": (0.0, None), "ctr": (0.5, "middle"), "r": (1.0, "end"), "just": (0.0, None)}
"""DrawingML paragraph alignment: share of the text box width the line is placed at, and its text-anchor."""
VERTICAL_ANCHORS: Final = {"t": 0.0, "ctr": 0.5, "b": 1.0}
"""DrawingML text body anchor: share of the free height above the text."""
SCHEME_ALIASES: Final = {"bg1": "lt1", "tx1": "dk1", "bg2": "lt2", "tx2": "dk2"}
"""Theme colour names used in shapes and the colour-scheme slots they stand for."""
STYLE_LINE_WIDTH: Final = 1.0 / PT_PER_INCH * PX_PER_INCH
"""Outline width (1 pt, in user units) of a shape painted by its style's line reference."""
THEME_RELATIONSHIP: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
"""Relationship type from a slide master to its theme."""
