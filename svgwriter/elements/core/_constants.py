"""
Constants for the element base: attribute tables, name checks, suggestions and preview sizes.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "COLOR_ATTRIBUTES",
    "COLOR_OPACITY",
    "HREF_ATTRIBUTES",
    "INLINE_STYLE",
    "INSTANCE_FIELDS",
    "OPEN_PREFIXES",
    "PREVIEW_MIN_PIXELS",
    "PREVIEW_PADDING",
    "PREVIEW_SCALE",
    "REPR_WIDTH",
    "XML_NAME_RE",
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

PREVIEW_PADDING: Final = 2.0
PREVIEW_SCALE: Final = 1.0
PREVIEW_MIN_PIXELS: Final = 200.0
REPR_WIDTH: Final = 120
INLINE_STYLE: Final = "display:inline-block;max-width:100%;overflow:auto;line-height:0"
