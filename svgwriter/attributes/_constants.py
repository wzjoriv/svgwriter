"""
Constants for ``svgwriter.attributes``: defaults, tables and patterns.
"""

from __future__ import annotations

import math
import re
from typing import Final

__all__ = [
    "ANGLE_RE",
    "AT_BLOCK_RE",
    "COMBINATORS",
    "COMMENT_RE",
    "COMPOUND_RE",
    "DEGREES_PER",
    "FUNC_IRI_RE",
    "IMPORTANT",
    "LENGTH_RE",
    "MARKER_LONGHANDS",
    "PLAIN_ATTRIBUTES",
    "PREFIXES",
    "RULE_RE",
    "SEPARATORS",
]

MARKER_LONGHANDS: Final = ("marker-start", "marker-mid", "marker-end")

DEGREES_PER: Final = {"deg": 1.0, "rad": 180.0 / math.pi, "grad": 0.9, "turn": 360.0}
ANGLE_RE: Final = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*(deg|rad|grad|turn)?\s*$")

COMMENT_RE: Final = re.compile(r"/\*.*?\*/", re.S)
RULE_RE: Final = re.compile(r"([^{}@]+)\{([^}]*)\}")
AT_BLOCK_RE: Final = re.compile(r"@[^{;]+(\{(?:[^{}]|\{[^{}]*\})*\}|;)")
COMPOUND_RE: Final = re.compile(r"(\*|[A-Za-z][\w-]*)|#([\w-]+)|\.([\w-]+)|\[([\w:-]+)(?:([~|]?=)\"?([^\"\]]*)\"?)?\]|(:[\w-]+(?:\([^)]*\))?)")
IMPORTANT: Final = "!important"

LENGTH_RE: Final = re.compile(
    r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*(px|pt|pc|mm|cm|in|em|ex|%)?\s*$"
)

PLAIN_ATTRIBUTES: Final = frozenset(
    {
        "accent-height", "accumulate", "additive", "alphabetic", "amplitude",
        "arabic-form", "ascent", "azimuth", "bbox", "begin", "bias", "by",
        "cap-height", "class", "cx", "cy", "d", "descent", "divisor", "dur",
        "dx", "dy", "elevation", "end", "exponent", "format", "from", "fr",
        "fx", "fy", "g1", "g2", "glyph-name", "hanging", "height",
        "horiz-adv-x", "horiz-origin-x", "horiz-origin-y", "id", "ideographic",
        "in", "in2", "intercept", "k", "k1", "k2", "k3", "k4", "lang",
        "local", "mathematical", "max", "media", "method", "min", "mode",
        "name", "offset", "operator", "order", "orient", "orientation",
        "origin", "overline-position", "overline-thickness",
        "panose-1", "path", "points", "r", "radius", "rendering-intent",
        "restart", "result", "rotate", "rx", "ry", "scale", "seed", "slope",
        "spacing", "stemh", "stemv", "strikethrough-position",
        "strikethrough-thickness", "string", "style", "target", "title",
        "to", "transform", "type", "u1", "u2", "underline-position",
        "underline-thickness", "unicode", "unicode-range", "units-per-em",
        "v-alphabetic", "v-hanging", "v-ideographic", "v-mathematical",
        "values", "version", "vert-adv-y", "vert-origin-x", "vert-origin-y",
        "visibility", "width", "widths", "x", "x-height", "x1", "x2", "y",
        "y1", "y2", "z", "zoomAndPan",
        "xlink:href", "xlink:title", "xlink:show", "xlink:actuate",
        "xlink:role", "xlink:arcrole", "xlink:type", "xml:base",
        "xml:lang", "xml:space",
    }
)
PREFIXES: Final = ("xlink", "xml")

FUNC_IRI_RE: Final = re.compile(r"""^\s*url\(\s*(['"]?)(.*?)\1\s*\)\s*$""")

SEPARATORS: Final = re.compile(r"[\s,]+")
COMBINATORS: Final = frozenset({">", "+", "~"})
