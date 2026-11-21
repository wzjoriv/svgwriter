"""
Constants for ``svgwriter.attributes``: defaults, tables and patterns.
"""

from __future__ import annotations

import math
import re
from typing import Final

__all__ = [
    "ROOT_RULES",
    "ANGLE_ATTRIBUTES",
    "ANGLE_RE",
    "ANGLE_SPELLINGS",
    "LENGTH_ATTRIBUTES",
    "LENGTH_SCALES",
    "LENGTH_SPELLINGS",
    "SUPERSCRIPTS",
    "AT_BLOCK_RE",
    "COMBINATORS",
    "COMMENT_RE",
    "COMPOUND_RE",
    "DEGREES_PER",
    "FULL_TURN_DEGREES",
    "FUNC_IRI_RE",
    "HALF_TURN_DEGREES",
    "IMPORTANT",
    "LENGTH_RE",
    "CSS_DIMENSION_RE",
    "MARKER_LONGHANDS",
    "PLAIN_ATTRIBUTES",
    "PREFIXES",
    "RULE_RE",
    "SEPARATORS",
    "EQUAL_DIGITS",
]

MARKER_LONGHANDS: Final = ("marker-start", "marker-mid", "marker-end")

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
}
LENGTH_SCALES: Final = {"m": ("mm", 1000.0), "ft": ("in", 12.0)}

ANGLE_ATTRIBUTES: Final = frozenset({"rotate", "azimuth", "elevation", "limitingConeAngle", "orient"})
LENGTH_ATTRIBUTES: Final = frozenset({
    "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "fx", "fy", "fr", "dx", "dy",
    "width", "height", "stroke-width", "stroke-dashoffset", "font-size", "letter-spacing",
    "word-spacing", "textLength", "startOffset", "markerWidth", "markerHeight", "refX", "refY",
})
SUPERSCRIPTS: Final = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")

COMMENT_RE: Final = re.compile(r"/\*.*?\*/", re.S)
RULE_RE: Final = re.compile(r"([^{}@]+)\{([^}]*)\}")
AT_BLOCK_RE: Final = re.compile(r"@[^{;]+(\{(?:[^{}]|\{[^{}]*\})*\}|;)")
COMPOUND_RE: Final = re.compile(r"(\*|[A-Za-z][\w-]*)|#([\w-]+)|\.([\w-]+)|\[([\w:-]+)(?:([~|]?=)\"?([^\"\]]*)\"?)?\]|(:[\w-]+(?:\([^)]*\))?)")
IMPORTANT: Final = "!important"
ROOT_RULES: Final = "_class_rules"
"""Root attribute holding style rules by class name that apply as if they led the first ``<style>`` (a theme)."""

CSS_DIMENSION_RE: Final = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)([A-Za-z]+)\s*$")
LENGTH_RE: Final = re.compile(
    r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*([A-Za-z]+|%)?\s*$"
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
PREFIXES: Final = ("xlink", "xml", "inkscape", "sodipodi")

FUNC_IRI_RE: Final = re.compile(r"""^\s*url\(\s*(['"]?)(.*?)\1\s*\)\s*$""")

SEPARATORS: Final = re.compile(r"[\s,]+")
COMBINATORS: Final = frozenset({">", "+", "~"})
