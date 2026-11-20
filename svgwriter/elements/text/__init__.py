"""
Text content elements, live character handles and SVG fonts.
"""

from __future__ import annotations

from ._character import Character, CharacterRange
from ._fonts import (
    Font,
    FontFace,
    FontFaceFormat,
    FontFaceName,
    FontFaceSrc,
    FontFaceUri,
    Glyph,
    HKern,
    MissingGlyph,
    VKern,
)
from ._text import AltGlyph, AltGlyphDef, AltGlyphItem, GlyphRef, Text, TextDecoration, TextPath, TRef, TSpan

__all__ = [
    "AltGlyph",
    "AltGlyphDef",
    "AltGlyphItem",
    "Character",
    "CharacterRange",
    "Font",
    "FontFace",
    "FontFaceFormat",
    "FontFaceName",
    "FontFaceSrc",
    "FontFaceUri",
    "Glyph",
    "GlyphRef",
    "HKern",
    "MissingGlyph",
    "TRef",
    "TSpan",
    "Text",
    "TextDecoration",
    "TextPath",
    "VKern",
]
