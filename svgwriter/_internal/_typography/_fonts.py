"""
Font resolution: registered faces, generic families and system fallbacks.
"""

from __future__ import annotations

import sys
import warnings
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import skia

from .._constants import (
    BOLD_WEIGHT,
    COLOR_GLYPH_TABLES,
    DEFAULT_FAMILY,
    DEFAULT_FONT_SIZE,
    EMOJI_JOINERS,
    EMOJI_MODIFIERS,
    EMOJI_PROBE,
    FONT_CACHE,
    FONT_SIZE_KEYWORDS,
    FONT_WEIGHTS,
    GENERIC_CANDIDATES,
    GENERIC_FAMILIES,
    GLYPH_CACHE,
    MAC_FALLBACK_FAMILIES,
    NORMAL_WEIGHT,
    NORMAL_WIDTH,
    PERCENT,
)
from ._font_match import FaceStyle, instance, match_rank

if TYPE_CHECKING:
    from ...ops.text import FontWeight

__all__ = ["cluster_font", "color_font", "font_for", "font_size", "font_weight", "registered_face", "registered_typefaces", "resolve_font", "weight_value"]


def font_weight(value: object) -> int:
    """A ``font-weight`` value (keyword or number) as a number."""
    text = str(value).strip()
    return FONT_WEIGHTS.get(text, int(text) if text.isdigit() else FONT_WEIGHTS["normal"])


def font_size(value: object) -> float:
    """A ``font-size`` value (keyword, length or percentage of the default) in user units."""
    from ...attributes.length import Length, Unit

    text = str(value).strip()
    if text in FONT_SIZE_KEYWORDS:
        return FONT_SIZE_KEYWORDS[text]
    try:
        size = Length.parse(value)
    except ValueError:
        return DEFAULT_FONT_SIZE
    return size.value * DEFAULT_FONT_SIZE / PERCENT if size.unit is Unit.PERCENT else size.to_user_units()


def weight_value(value: FontWeight) -> int:
    """A CSS font weight as a number."""
    if value == "normal":
        return NORMAL_WEIGHT
    if value == "bold":
        return BOLD_WEIGHT
    return int(value)


registered_typefaces: dict[str, list[tuple[Any, FaceStyle]]] = {}
_COLOR_FACES: dict[int, bool] = {}


def color_font(typeface: Any) -> bool:
    """Whether *typeface* draws glyphs in colour (COLR, sbix, CBDT or SVG tables), as emoji fonts do."""
    key = typeface.uniqueID()
    if key not in _COLOR_FACES:
        _COLOR_FACES[key] = any(typeface.copyTableData(int.from_bytes(tag.encode("latin-1"), "big")) is not None
                                for tag in COLOR_GLYPH_TABLES)
    return _COLOR_FACES[key]


def registered_face(family: str, weight: int, italic: bool) -> Any:
    """The registered typeface of *family* that CSS font matching picks for the weight and slant, if any.

    Variable faces come back set to the requested weight.
    """
    faces = registered_typefaces.get(family.lower())
    if not faces:
        return None
    style = "italic" if italic else "normal"
    typeface, face = min(faces, key=lambda entry: match_rank(entry[1], weight, style))
    return instance(typeface, face, weight, style)


@lru_cache(maxsize=FONT_CACHE)
def resolve_font(font_family: str, size: float, weight: FontWeight, italic: bool) -> Any:
    """The skia font for a CSS family list, weight and slant; warns when the family is missing."""
    slant = skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant
    families = [name.strip().strip("'\"") for name in font_family.split(",") if name.strip()]
    for family in families:
        face = registered_face(family, weight_value(weight), italic)
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
    >>> from svgwriter._internal._typography._fonts import font_for
    >>> font_for("A", "sans-serif", 16).getSize()
    16.0
    """
    font = resolve_font(font_family, size, weight, italic)
    if not char or font.unicharToGlyph(ord(char[0])):
        return font
    slant = skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant
    style = skia.FontStyle(weight_value(weight), NORMAL_WIDTH, slant)
    if sys.platform == "darwin":
        name = _scanned_family(ord(char[0]), weight_value(weight), italic)
    else:
        family = font.getTypeface().getFamilyName()
        hints = [language] if language else []
        match = skia.FontMgr.RefDefault().matchFamilyStyleCharacter(family, style, hints, ord(char[0]))
        name = match.getFamilyName() if match is not None else None
    if name is None:
        return font
    return skia.Font(skia.Typeface(name, style), size)


@lru_cache(maxsize=GLYPH_CACHE)
def _scanned_family(code: int, weight: int, italic: bool) -> str | None:
    """The first installed family with a glyph for *code*: common macOS fallbacks first, then all families.

    skia-python's character matching crashes on macOS, so fallback there searches the families itself.
    """
    manager = skia.FontMgr.RefDefault()
    slant = skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant
    style = skia.FontStyle(weight, NORMAL_WIDTH, slant)
    installed = [manager.getFamilyName(index) for index in range(manager.countFamilies())]
    for name in dict.fromkeys([*MAC_FALLBACK_FAMILIES, *installed]):
        typeface = skia.Typeface(name, style)
        if typeface.getFamilyName().lower() == name.lower() and skia.Font(typeface).unicharToGlyph(code):
            return name
    return None


def cluster_font(cluster: str, font_family: str, size: float, weight: FontWeight = "normal", italic: bool = False,
                 language: str | None = None) -> Any:
    """The font for one grapheme cluster: like :func:`font_for`, but an emoji sequence picks the emoji font.

    A cluster that asks for emoji presentation (variation selector 16, keycap, ZWJ or skin tone) is
    drawn from the colour emoji font when that font has its first character, so ``"1\ufe0f\u20e3"``
    is a keycap rather than a digit.

    Parameters
    ----------
    cluster : str
        One user-perceived character, possibly several code points.
    font_family : str
        CSS font family list.
    size : float
        Font size in user units.
    weight : {"normal", "bold"} or int, optional
        Font weight. Defaults to "normal".
    italic : bool, optional
        Prefer an italic face. Defaults to False.
    language : str, optional
        BCP 47 language hint. Defaults to None.

    Returns
    -------
    skia.Font
        The font that draws the cluster.

    Examples
    --------
    >>> from svgwriter._internal._typography._fonts import cluster_font
    >>> cluster_font("A", "sans-serif", 16).getSize()
    16.0
    """
    font = font_for(cluster[:1], font_family, size, weight, italic, language)
    if not any(char in EMOJI_JOINERS or EMOJI_MODIFIERS[0] <= ord(char) <= EMOJI_MODIFIERS[1] for char in cluster[1:]):
        return font
    emoji = font_for(EMOJI_PROBE, font_family, size, weight, italic, language)
    if color_font(emoji.getTypeface()) and emoji.unicharToGlyph(ord(cluster[0])):
        return emoji
    return font
