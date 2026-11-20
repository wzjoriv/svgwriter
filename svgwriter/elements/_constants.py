"""
Constants shared by the element modules: attribute tables, text defaults and preview sizes.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "COLOR_ATTRIBUTES",
    "COLOR_OPACITY",
    "DEFAULT_FONT_FAMILY",
    "DEFAULT_FONT_SIZE",
    "DEFAULT_STROKE_WIDTH",
    "FONT_SIZE_KEYWORDS",
    "FONT_WEIGHTS",
    "HREF_ATTRIBUTES",
    "INLINE_STYLE",
    "INSTANCE_FIELDS",
    "JOINING_RANGES",
    "NOT_COPIED",
    "OPEN_PREFIXES",
    "PERCENT",
    "POSITIONING",
    "POSITION_NAMES",
    "PREVIEW_MIN_PIXELS",
    "PREVIEW_PADDING",
    "PREVIEW_SCALE",
    "REGIONAL_INDICATORS",
    "REPR_WIDTH",
    "SUGGESTIONS",
    "WHITESPACE_DEFAULT",
    "WHITESPACE_PRESERVE",
    "XML_NAME_RE",
    "ZWJ",
]

HREF_ATTRIBUTES: Final = frozenset({"xlink:href"})
COLOR_OPACITY: Final = {
    "fill": "fill-opacity",
    "stroke": "stroke-opacity",
    "stop-color": "stop-opacity",
    "flood-color": "flood-opacity",
}
COLOR_ATTRIBUTES: Final = frozenset({*COLOR_OPACITY, "color", "lighting-color"})
XML_NAME_RE: Final = re.compile(r"^[A-Za-z_][\w.\-]*$")
OPEN_PREFIXES: Final = ("data-", "aria-")
INSTANCE_FIELDS: Final = frozenset({"attributes", "children", "parent"})

NOT_COPIED: Final = frozenset({"id", "transform", "clip-path"})
DEFAULT_STROKE_WIDTH: Final = 1.0
SUGGESTIONS: Final = 3

PREVIEW_PADDING: Final = 2.0
PREVIEW_SCALE: Final = 1.0
PREVIEW_MIN_PIXELS: Final = 200.0
REPR_WIDTH: Final = 120
INLINE_STYLE: Final = "display:inline-block;max-width:100%;overflow:auto;line-height:0"

POSITIONING: Final = ("x", "y", "dx", "dy", "rotate")
PERCENT: Final = 100.0
POSITION_NAMES: Final = ("x", "y", "dx", "dy", "rotate")
DEFAULT_FONT_FAMILY: Final = "sans-serif"
DEFAULT_FONT_SIZE: Final = 16.0
FONT_WEIGHTS: Final = {"normal": 400, "bold": 700, "bolder": 700, "lighter": 300}
FONT_SIZE_KEYWORDS: Final = {"xx-small": 9.0, "x-small": 10.0, "small": 13.0, "medium": 16.0, "large": 18.0,
                             "x-large": 24.0, "xx-large": 32.0, "smaller": 13.0, "larger": 19.0}
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
