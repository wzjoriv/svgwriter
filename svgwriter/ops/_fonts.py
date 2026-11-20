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
    NORMAL_WEIGHT,
    NORMAL_WIDTH,
)

if TYPE_CHECKING:
    from .text import FontWeight

__all__ = ["registered_face", "registered_typefaces", "resolve_font", "weight_value"]


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
