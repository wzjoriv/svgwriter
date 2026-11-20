"""
Font resolution: registered faces, generic families and system fallbacks.
"""

from __future__ import annotations

import warnings
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import skia

from ._constants import (
    BOLD_WEIGHT,
    DEFAULT_FAMILY,
    FONT_CACHE,
    GENERIC_CANDIDATES,
    GENERIC_FAMILIES,
    GLYPH_CACHE,
    NORMAL_WEIGHT,
    NORMAL_WIDTH,
)

if TYPE_CHECKING:
    from .text import FontWeight

__all__ = ["font_for", "registered_face", "registered_typefaces", "resolve_font", "weight_value"]


def weight_value(value: FontWeight) -> int:
    """A CSS font weight as a number."""
    if value == "normal":
        return NORMAL_WEIGHT
    if value == "bold":
        return BOLD_WEIGHT
    return int(value)


registered_typefaces: dict[str, list[Any]] = {}


def registered_face(family: str, weight: int, slant: Any) -> Any:
    """The registered typeface of *family* closest to the requested weight and slant, if any."""
    faces = registered_typefaces.get(family.lower())
    if not faces:
        return None
    return min(faces, key=lambda face: (face.fontStyle().slant() != slant, abs(face.fontStyle().weight() - weight)))


@lru_cache(maxsize=FONT_CACHE)
def resolve_font(font_family: str, size: float, weight: FontWeight, italic: bool) -> Any:
    """The skia font for a CSS family list, weight and slant; warns when the family is missing."""
    slant = skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant
    families = [name.strip().strip("'\"") for name in font_family.split(",") if name.strip()]
    for family in families:
        face = registered_face(family, weight_value(weight), slant)
        if face is not None:
            return skia.Font(face, size)
    typeface = None
    for family in families or [DEFAULT_FAMILY]:
        for concrete in GENERIC_CANDIDATES.get(family.lower(), ()):
            match = skia.Typeface(concrete, skia.FontStyle(weight_value(weight), NORMAL_WIDTH, slant))
            if match.getFamilyName().lower() == concrete.lower():
                return skia.Font(match, size)
        candidate = skia.Typeface(family, skia.FontStyle(weight_value(weight), NORMAL_WIDTH, slant))
        if family.lower() in GENERIC_FAMILIES or candidate.getFamilyName().lower() == family.lower():
            typeface = candidate
            break
    if typeface is None:
        typeface = skia.Typeface(families[-1], skia.FontStyle(weight_value(weight), NORMAL_WIDTH, slant))
        warnings.warn(
            f"font {font_family!r} not found; using {typeface.getFamilyName()!r}",
            stacklevel=3,
        )
    return skia.Font(typeface, size)


@lru_cache(maxsize=GLYPH_CACHE)
def font_for(char: str, font_family: str, size: float, weight: FontWeight = "normal", italic: bool = False,
             language: str | None = None) -> Any:
    """The font for *char*: the requested family when it has the glyph, else a system font that does.

    Like a browser, layout falls back per character, so Devanagari, Bengali,
    CJK and other scripts render even when the chosen family lacks them.

    Parameters
    ----------
    char : str
        The character (first code point is used).
    font_family : str
        CSS font family list.
    size : float
        Font size in user units.
    weight : {"normal", "bold"} or int, optional
        Font weight. Defaults to "normal".
    italic : bool, optional
        Prefer an italic face. Defaults to False.
    language : str, optional
        BCP 47 language hint (``"zh"``, ``"ja"``, ...) for choosing among fonts
        that cover the character. Defaults to None.

    Returns
    -------
    skia.Font
        A font that can draw *char*, or the requested one when nothing can.

    Examples
    --------
    >>> from svgwriter.ops._fonts import font_for
    >>> font_for("A", "sans-serif", 16).getSize()
    16.0
    """
    font = resolve_font(font_family, size, weight, italic)
    if not char or font.unicharToGlyph(ord(char[0])):
        return font
    slant = skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant
    style = skia.FontStyle(weight_value(weight), NORMAL_WIDTH, slant)
    family = font.getTypeface().getFamilyName()
    hints = [language] if language else []
    fallback = skia.FontMgr.RefDefault().matchFamilyStyleCharacter(family, style, hints, ord(char[0]))
    if fallback is None:
        return font
    return skia.Font(skia.Typeface(fallback.getFamilyName(), style), size)
