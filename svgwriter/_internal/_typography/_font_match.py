"""
Font faces as CSS sees them: weight, style and stretch ranges, matching and variable instances.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Literal

import skia

from ._font_constants import (
    AXIS_SLANT,
    AXIS_WEIGHT,
    AXIS_WIDTH,
    MATCH_WEIGHT_HIGH,
    MATCH_WEIGHT_LOW,
    NORMAL_STRETCH,
    STYLE_ORDER,
    STYLES,
    SUBFAMILY_STYLES,
    TAG_BYTES,
    WIDTH_PERCENT,
)

__all__ = ["STATIC_FONTS", "FaceStyle", "FontStyle", "Range", "axis_tag", "describe", "instance", "match_rank",
           "static_font", "static_fonts", "static_instance", "style_of"]

FontStyle = Literal["normal", "italic", "oblique"]
Range = tuple[float, float]


def axis_tag(tag: int | str) -> str | int:
    """An OpenType axis tag as text (``"wght"``) from skia's integer, or the integer from text."""
    if isinstance(tag, str):
        return int.from_bytes(tag.encode("latin-1"), "big")
    return tag.to_bytes(TAG_BYTES, "big").decode("latin-1")


@dataclass(frozen=True)
class FaceStyle:
    """The CSS descriptors of one face: weight and stretch ranges, style and variation axes."""

    weight: Range
    style: FontStyle
    stretch: Range
    axes: dict[str, tuple[float, float, float]] = field(default_factory=dict)

    @property
    def styles(self) -> frozenset[str]:
        """The styles this face can draw: its own, plus oblique when a slant axis leans."""
        slant = self.axes.get(AXIS_SLANT)
        return frozenset({self.style, "oblique"} if slant and slant[0] < 0 else {self.style})


def style_of(value: object) -> FontStyle:
    """A ``font-style`` value (keyword, bool for italic, or skia slant) as a CSS keyword."""
    if isinstance(value, bool):
        return "italic" if value else "normal"
    if isinstance(value, skia.FontStyle.Slant):
        return STYLES[int(value)]  # type: ignore[return-value]
    text = str(value).strip().split()[0] if str(value).strip() else "normal"
    if text not in STYLES:
        raise ValueError(f"unknown font style {value!r}; expected one of {STYLES}")
    return text  # type: ignore[return-value]


def variation_axes(typeface: Any) -> list[Any]:
    """The variation axes of a skia typeface; empty for a static font (some skia builds raise for those)."""
    try:
        return list(typeface.getVariationDesignParameters())
    except RuntimeError:
        return []


def describe(typeface: Any, weight: float | Range | None = None, style: str | None = None,
             stretch: float | Range | None = None, subfamily: str = "") -> FaceStyle:
    """The CSS descriptors of a skia typeface, read from the font unless given.

    Weight and width come from the OS/2 table or the variation axes; the style from the OS/2
    selection flags, with an italic or oblique subfamily name winning over an upright flag.
    """
    axes = {str(axis_tag(axis.tag)): (axis.min, getattr(axis, "def"), axis.max)
            for axis in variation_axes(typeface)}
    font_style = typeface.fontStyle()
    if weight is None:
        weight = axes[AXIS_WEIGHT][0::2] if AXIS_WEIGHT in axes else font_style.weight()
    if stretch is None:
        stretch = axes[AXIS_WIDTH][0::2] if AXIS_WIDTH in axes else WIDTH_PERCENT.get(font_style.width(), NORMAL_STRETCH)
    if style is None:
        style = style_of(font_style.slant())
        named = [word for word in SUBFAMILY_STYLES if word in subfamily.lower()]
        style = named[0] if style == "normal" and named else style
    return FaceStyle(_range(weight), style_of(style), _range(stretch), axes)


def _range(value: float | Range) -> Range:
    if isinstance(value, tuple):
        return (float(value[0]), float(value[1]))
    return (float(value), float(value))


def _nearest(span: Range, value: float) -> float:
    return min(max(value, span[0]), span[1])


def _weight_rank(span: Range, weight: float) -> tuple[int, float]:
    """CSS Fonts 4 weight matching: inside the range first, then the search order around 400-500."""
    candidate = _nearest(span, weight)
    if candidate == weight:
        return (0, 0.0)
    if weight > MATCH_WEIGHT_HIGH:
        return (1, candidate - weight) if candidate > weight else (2, weight - candidate)
    if weight < MATCH_WEIGHT_LOW:
        return (1, weight - candidate) if candidate < weight else (2, candidate - weight)
    if weight < candidate <= MATCH_WEIGHT_HIGH:
        return (1, candidate - weight)
    return (2, weight - candidate) if candidate < weight else (3, candidate - weight)


def _stretch_rank(span: Range) -> tuple[int, float]:
    candidate = _nearest(span, NORMAL_STRETCH)
    if candidate == NORMAL_STRETCH:
        return (0, 0.0)
    return (1, NORMAL_STRETCH - candidate) if candidate < NORMAL_STRETCH else (2, candidate - NORMAL_STRETCH)


def match_rank(face: FaceStyle, weight: float, style: str) -> tuple[Any, ...]:
    """Sort key of *face* for a request: stretch, then style, then weight, as CSS font matching orders them."""
    order = STYLE_ORDER[style]
    style_rank = min(order.index(own) for own in face.styles)
    return (_stretch_rank(face.stretch), style_rank, _weight_rank(face.weight, weight))


def instance(typeface: Any, face: FaceStyle, weight: float, style: str) -> Any:
    """*typeface* set to the requested weight (and slant) when it is variable; itself otherwise."""
    position = {}
    if AXIS_WEIGHT in face.axes:
        position[AXIS_WEIGHT] = _nearest(face.weight, weight)
    slant = face.axes.get(AXIS_SLANT)
    if slant and style != "normal" and face.style == "normal" and slant[0] < 0:
        position[AXIS_SLANT] = slant[0]
    if not position:
        return typeface
    coordinates = skia.FontArguments.VariationPosition.Coordinates(
        [skia.FontArguments.VariationPosition.Coordinate(axis_tag(tag), value) for tag, value in position.items()])
    arguments = skia.FontArguments()
    arguments.setVariationDesignPosition(skia.FontArguments.VariationPosition(coordinates))
    return typeface.makeClone(arguments)


STATIC_FONTS: ContextVar[bool] = ContextVar("svgwriter_static_fonts", default=False)
"""True while writing a format that needs static fonts (PDF): variable faces are then instanced."""


@contextmanager
def static_fonts() -> Iterator[None]:
    """Instance variable fonts at their used position for the block, so PDF embeds them as TrueType."""
    token = STATIC_FONTS.set(True)
    try:
        yield
    finally:
        STATIC_FONTS.reset(token)


def static_font(font: Any) -> Any:
    """*font* with a static copy of its typeface when that is variable and static fonts are on; else *font*."""
    typeface = font.getTypeface() if STATIC_FONTS.get() else None
    if typeface is None or not variation_axes(typeface):
        return font
    position = {str(axis_tag(coordinate.axis)): coordinate.value
                for coordinate in typeface.getVariationDesignPosition()}
    static = static_instance(typeface, position)
    if static is None:
        return font
    copy = font.makeWithSize(font.getSize())
    copy.setTypeface(static)
    return copy


def static_instance(typeface: Any, position: dict[str, float]) -> Any:
    """A static (non-variable) copy of *typeface* at *position*, or None when fontTools is missing."""
    key = (typeface.getFamilyName(), typeface.uniqueID(), tuple(sorted(position.items())))
    if key not in _STATIC:
        _STATIC[key] = _instanced(typeface, position)
    return _STATIC[key]


def _instanced(typeface: Any, position: dict[str, float]) -> Any:
    try:
        from fontTools.ttLib import TTFont
        from fontTools.varLib.instancer import instantiateVariableFont
    except ImportError:
        return None
    from ._sfnt import sfnt_bytes

    data = sfnt_bytes(typeface)
    try:
        try:
            font = instantiateVariableFont(TTFont(io.BytesIO(data)), position, updateFontNames=True)
        except Exception:  # noqa: BLE001 - fonts without a STAT table cannot be renamed; keep their names
            font = instantiateVariableFont(TTFont(io.BytesIO(data)), position)
        out = io.BytesIO()
        font.save(out)
    except Exception:  # noqa: BLE001 - a font fontTools cannot instance keeps its variable form
        return None
    return skia.Typeface.MakeFromData(skia.Data.MakeWithCopy(out.getvalue()))


_STATIC: dict[tuple[Any, ...], Any] = {}
"""Static instances made so far, by family, typeface id and position."""
