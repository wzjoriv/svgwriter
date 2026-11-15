"""Mapping between Python keyword names and SVG attribute names."""

from __future__ import annotations

from functools import lru_cache
from typing import Final

__all__ = [
    "CAMEL_CASE_ATTRIBUTES",
    "KNOWN_ATTRIBUTES",
    "EVENT_ATTRIBUTES",
    "PRESENTATION_ATTRIBUTES",
    "UNSUPPORTED_ATTRIBUTES",
    "py_name",
    "svg_name",
]

CAMEL_CASE_ATTRIBUTES: Final = frozenset(
    {
        "attributeName", "attributeType", "baseFrequency", "baseProfile",
        "calcMode", "clipPathUnits", "contentStyleType",
        "diffuseConstant", "edgeMode", "externalResourcesRequired",
        "filterRes", "filterUnits", "glyphRef", "gradientTransform",
        "gradientUnits", "kernelMatrix", "kernelUnitLength", "keyPoints",
        "keySplines", "keyTimes", "lengthAdjust", "limitingConeAngle",
        "markerHeight", "markerUnits", "markerWidth", "maskContentUnits",
        "maskUnits", "numOctaves", "pathLength", "patternContentUnits",
        "patternTransform", "patternUnits", "pointsAtX", "pointsAtY",
        "pointsAtZ", "preserveAlpha", "preserveAspectRatio", "primitiveUnits",
        "refX", "refY", "repeatCount", "repeatDur", "requiredExtensions",
        "requiredFeatures", "specularConstant", "specularExponent",
        "spreadMethod", "startOffset", "stdDeviation", "stitchTiles",
        "surfaceScale", "systemLanguage", "tableValues", "targetX", "targetY",
        "textLength", "viewBox", "viewTarget", "xChannelSelector",
        "yChannelSelector", "zoomAndPan",
    }
)

PRESENTATION_ATTRIBUTES: Final = frozenset(
    {
        "alignment-baseline", "baseline-shift", "clip", "clip-path",
        "clip-rule", "color", "color-interpolation",
        "color-interpolation-filters", "color-profile", "color-rendering",
        "direction", "display", "dominant-baseline",
        "enable-background", "fill", "fill-opacity", "fill-rule", "filter",
        "flood-color", "flood-opacity", "font", "font-family", "font-size",
        "font-size-adjust", "font-stretch", "font-style", "font-variant",
        "font-weight", "glyph-orientation-horizontal",
        "glyph-orientation-vertical", "image-rendering", "kerning",
        "letter-spacing", "lighting-color", "marker", "marker-end",
        "marker-mid", "marker-start", "mask", "opacity", "overflow",
        "pointer-events", "shape-rendering", "stop-color", "stop-opacity",
        "stroke", "stroke-dasharray", "stroke-dashoffset", "stroke-linecap",
        "stroke-linejoin", "stroke-miterlimit", "stroke-opacity",
        "stroke-width", "text-anchor", "text-decoration", "text-rendering",
        "unicode-bidi", "visibility", "word-spacing", "writing-mode",
    }
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

EVENT_ATTRIBUTES: Final = frozenset(
    {
        "onabort", "onactivate", "onbegin", "onclick", "onend", "onerror",
        "onfocusin", "onfocusout", "onload", "onmousedown", "onmousemove",
        "onmouseout", "onmouseover", "onmouseup", "onrepeat", "onresize",
        "onscroll", "onunload", "onzoom",
    }
)
"""Scripting hooks; svgwriter writes static graphics and rejects them."""

UNSUPPORTED_ATTRIBUTES: Final = EVENT_ATTRIBUTES | {"cursor", "contentScriptType"}
KNOWN_ATTRIBUTES: Final = CAMEL_CASE_ATTRIBUTES | PRESENTATION_ATTRIBUTES | PLAIN_ATTRIBUTES
"""Every SVG 1.1 attribute name svgwriter writes (web-only ones excluded)."""

_PREFIXES: Final = ("xlink", "xml")
_CAMEL_LOOKUP: Final = {
    name.lower(): name for name in CAMEL_CASE_ATTRIBUTES
}


@lru_cache(maxsize=1024)
def svg_name(name: str) -> str:
    """Translate a Python keyword (``stroke_width``) into an SVG name.

    Trailing underscores are dropped (``class_``, ``in_``), ``xlink_`` and
    ``xml_`` become namespace prefixes, known camelCase attributes are
    restored, and remaining underscores become hyphens.
    """
    name = name.rstrip("_")
    if ":" in name or name in CAMEL_CASE_ATTRIBUTES:
        return name
    for prefix in _PREFIXES:
        if name.startswith(prefix + "_"):
            return f"{prefix}:{name[len(prefix) + 1:]}"
    compact = name.replace("_", "").lower()
    if compact in _CAMEL_LOOKUP:
        return _CAMEL_LOOKUP[compact]
    return name.replace("_", "-")


@lru_cache(maxsize=1024)
def py_name(name: str) -> str:
    """Translate an SVG attribute name into a Python keyword."""
    if name in CAMEL_CASE_ATTRIBUTES:
        return "".join("_" + c.lower() if c.isupper() else c for c in name)
    py = name.replace(":", "_").replace("-", "_")
    return py + "_" if py in ("class", "in", "from") else py
