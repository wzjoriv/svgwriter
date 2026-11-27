"""
Constants for ``svgwriter.model.attributes``: defaults, tables and patterns.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "ANY_TAG",
    "CLASS_KEY",
    "DESCENDANT",
    "FIRST_CHILD",
    "ID_KEY",
    "INLINE_CACHE_SIZE",
    "RULE_SET_CACHE_SIZE",
    "SELECTOR_CACHE_SIZE",
    "SHEET_CACHE_SIZE",
    "STYLE_MEMO",
    "TAG_KEY",
    "UNIVERSAL_KEY",
    "ROOT_RULES",
    "ANGLE_ATTRIBUTES",
    "LENGTH_ATTRIBUTES",
    "AT_BLOCK_RE",
    "COMBINATORS",
    "COMMENT_RE",
    "COMPOUND_RE",
    "FUNC_IRI_RE",
    "IMPORTANT",
    "CSS_DIMENSION_RE",
    "MARKER_LONGHANDS",
    "PLAIN_ATTRIBUTES",
    "PREFIXES",
    "RULE_RE",
    "SEPARATORS",
]

MARKER_LONGHANDS: Final = ("marker-start", "marker-mid", "marker-end")



ANGLE_ATTRIBUTES: Final = frozenset({"rotate", "azimuth", "elevation", "limitingConeAngle", "orient"})
LENGTH_ATTRIBUTES: Final = frozenset({
    "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "fx", "fy", "fr", "dx", "dy",
    "width", "height", "stroke-width", "stroke-dashoffset", "font-size", "letter-spacing",
    "word-spacing", "textLength", "startOffset", "markerWidth", "markerHeight", "refX", "refY",
})
PLAIN_VALUE_TYPES: Final = frozenset({str, int, float, bool})
"""Value types that carry no dimension, so no attribute refuses them."""

COMMENT_RE: Final = re.compile(r"/\*.*?\*/", re.S)
RULE_RE: Final = re.compile(r"([^{}@]+)\{([^}]*)\}")
AT_BLOCK_RE: Final = re.compile(r"@[^{;]+(\{(?:[^{}]|\{[^{}]*\})*\}|;)")
COMPOUND_RE: Final = re.compile(r"(\*|[A-Za-z][\w-]*)|#([\w-]+)|\.([\w-]+)|\[([\w:-]+)(?:([~|]?=)\"?([^\"\]]*)\"?)?\]|(:[\w-]+(?:\([^)]*\))?)")
IMPORTANT: Final = "!important"
ROOT_RULES: Final = "_class_rules"
"""Root attribute holding style rules by class name that apply as if they led the first ``<style>`` (a theme)."""

CSS_DIMENSION_RE: Final = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)([A-Za-z]+)\s*$")

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
DESCENDANT: Final = " "
ANY_TAG: Final = "*"
FIRST_CHILD: Final = ":first-child"
ID_KEY: Final = "#"
CLASS_KEY: Final = "."
TAG_KEY: Final = "tag"
UNIVERSAL_KEY: Final = "*"
"""Index buckets of a rule set, by the rightmost compound's id, first class, tag, or none of them."""
SELECTOR_CACHE_SIZE: Final = 4096
SHEET_CACHE_SIZE: Final = 256
RULE_SET_CACHE_SIZE: Final = 64
INLINE_CACHE_SIZE: Final = 4096
"""Bounds of the caches of compiled selectors, parsed sheets, indexed rule sets and parsed inline styles."""
STYLE_MEMO: Final = "_style_memo"
"""Element attribute holding its last matched declarations, with the key they are valid for."""
