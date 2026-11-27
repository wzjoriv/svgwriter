"""
Text content elements, live character handles and SVG fonts.
"""

from __future__ import annotations

from ._altglyph import AltGlyphDef, AltGlyphItem, GlyphRef
from ._character import Character, CharacterRange
from ._fontface import FontFace, FontFaceFormat, FontFaceName, FontFaceSrc, FontFaceUri
from ._fonts import Font, HKern, VKern
from ._glyphs import Glyph, MissingGlyph
from ._selection import CharacterSelection
from ._spans import TRef, TSpan
from ._text import Text, TextDecoration
from ._textpath import AltGlyph, TextPath

__all__ = [
    "AltGlyph",
    "AltGlyphDef",
    "AltGlyphItem",
    "Character",
    "CharacterRange",
    "CharacterSelection",
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
