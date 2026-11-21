"""
Text effects of materials and motion: metal, wind, neon and glitch.
"""

from __future__ import annotations

from ..color.color import ColorLike, as_color
from ..elements import (
    ColorMatrixType,
    CompositeOperator,
    FeColorMatrix,
    FeComposite,
    FeDistantLight,
    FeGaussianBlur,
    FeMerge,
    FeOffset,
    FeSpecularLighting,
    StandardInput,
    Text,
)
from ..gradients import blend, metallic
from ..preset import text_effect
from ..theme import Theme
from ._constants import (
    GLITCH_COLORS,
    GLITCH_DURATION,
    GLITCH_SHIFTS,
    METAL_DURATION,
    METAL_EDGE,
    METAL_LIGHT,
    METAL_ROUNDING,
    METAL_SHADOW,
    METAL_SWEEP,
    NEON_DURATION,
    NEON_FLICKER,
    NEON_GLOWS,
    NEON_STROKE,
    NEON_TUBE,
    WIND_COLORS,
    WIND_DURATION,
    WIND_GUSTS,
    WIND_STREAK,
)
from ._parts import fit, loop, tinted

__all__ = ["glitch", "metal", "neon", "wind"]


@text_effect
def metal(text: Text, *, base: ColorLike = "#a8adb5", animate: bool = True) -> None:
    """Polished metal letters: banded steel (or any *base*), a dark edge, a raised highlight and a shadow.

    Parameters
    ----------
    text : Text
        The text, or a range of it.
    base : Color or str, optional
        Metal color; ``"gold"`` or ``"#b87333"`` (copper) for others. Defaults to steel.
    animate : bool, optional
        Swing the light so the highlight moves. Defaults to True.

    Examples
    --------
    >>> import svgwriter as svg
    >>> title = svg.text("Metal", x=0, y=30, font_size=30)
    >>> svg.text_effects.metal(title, base="gold").fill.element.tag
    'linearGradient'
    """
    size = fit(text)
    text.fill = metallic(base)
    edge, width = METAL_EDGE
    text.stroke = edge
    text.stroke_width = size(width)
    elevation, shine_constant, exponent, depth = METAL_LIGHT
    light = FeDistantLight(azimuth=METAL_SWEEP[0], elevation=elevation)
    if animate:
        loop(light, "azimuth", size.values(METAL_SWEEP, frequency=True), METAL_DURATION)
    rim = FeGaussianBlur(size(METAL_ROUNDING), in_=StandardInput.SOURCE_ALPHA)
    shine = FeSpecularLighting(light, in_=rim, surface_scale=size(depth), specular_constant=shine_constant,
                               specular_exponent=exponent, lighting_color="white")
    inside = FeComposite(CompositeOperator.IN, in_=shine, in2=StandardInput.SOURCE_ALPHA)
    lit = FeComposite(CompositeOperator.ARITHMETIC, in_=StandardInput.SOURCE_GRAPHIC, in2=inside, k2=1, k3=1)
    distance, opacity = METAL_SHADOW
    drop = FeOffset(size(distance), size(distance), in_=rim)
    flood, shadow = tinted("black", drop, opacity)
    text.filter = size.filter(rim, shine, inside, lit, drop, flood, shadow, FeMerge(shadow, lit))


@text_effect
def wind(text: Text, *, animate: bool = True) -> None:
    """Windswept letters: pale air-blue glyphs trailing a gusting streak.

    Parameters
    ----------
    text : Text
        The text, or a range of it.
    animate : bool, optional
        Let the streak gust. Defaults to True.

    Examples
    --------
    >>> import svgwriter as svg
    >>> title = svg.text("Wind", x=0, y=30, font_size=30)
    >>> svg.text_effects.wind(title).get("filter").element[0].tag
    'feGaussianBlur'
    """
    size = fit(text)
    text.fill = blend(*WIND_COLORS, angle=90)
    blur, distance, opacity = WIND_STREAK
    smear = FeGaussianBlur((size(blur), 0), in_=StandardInput.SOURCE_GRAPHIC)
    trail = FeOffset(-size(distance), 0, in_=smear)
    if animate:
        loop(trail, "dx", size.values(WIND_GUSTS), WIND_DURATION)
    faded = FeColorMatrix(ColorMatrixType.MATRIX, [1.0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, opacity, 0],
                          in_=trail)
    text.filter = size.filter(smear, trail, faded, FeMerge(faded, StandardInput.SOURCE_GRAPHIC))


@text_effect
def neon(text: Text, *, color: ColorLike | None = None, animate: bool = True) -> None:
    """A neon tube: a pale core in *color*'s tint, layered glows of *color*, and the odd flicker.

    Parameters
    ----------
    text : Text
        The text, or a range of it.
    color : Color or str, optional
        Tube color. Defaults to None, the current theme's accent color.
    animate : bool, optional
        Flicker now and then. Defaults to True.

    Examples
    --------
    >>> import svgwriter as svg
    >>> title = svg.text("Open", x=0, y=30, font_size=30)
    >>> sum(child.tag == "feGaussianBlur" for child in svg.text_effects.neon(title).get("filter").element)
    3
    """
    size = fit(text)
    tube = as_color(color if color is not None else Theme.current().palette.accent)
    text.fill = tube.mix("white", NEON_TUBE)
    text.stroke = tube
    text.stroke_width = size(NEON_STROKE)
    primitives = []
    glows = []
    for radius in reversed(NEON_GLOWS):
        halo = FeGaussianBlur(size(radius), in_=StandardInput.SOURCE_ALPHA)
        flood, glow = tinted(tube, halo)
        primitives += [halo, flood, glow]
        glows.append(glow)
    text.filter = size.filter(*primitives, FeMerge(*glows, StandardInput.SOURCE_GRAPHIC))
    if animate:
        loop(text, "opacity", NEON_FLICKER, NEON_DURATION, discrete=True)


@text_effect
def glitch(text: Text, *, animate: bool = True) -> None:
    """A digital glitch: red and cyan copies of the glyphs jump apart and back.

    Parameters
    ----------
    text : Text
        The text, or a range of it.
    animate : bool, optional
        Jitter the copies. Defaults to True.

    Examples
    --------
    >>> import svgwriter as svg
    >>> title = svg.text("Error", x=0, y=30, font_size=30)
    >>> sum(child.tag == "feOffset" for child in svg.text_effects.glitch(title).get("filter").element)
    2
    """
    size = fit(text)
    primitives = []
    copies = []
    for color, sign in zip(GLITCH_COLORS, (1, -1), strict=True):
        flood, copy = tinted(color, StandardInput.SOURCE_ALPHA)
        shift = FeOffset(size(sign * GLITCH_SHIFTS[0]), 0, in_=copy)
        if animate:
            loop(shift, "dx", size.values(sign * value for value in GLITCH_SHIFTS), GLITCH_DURATION, discrete=True)
        primitives += [flood, copy, shift]
        copies.append(shift)
    text.filter = size.filter(*primitives, FeMerge(*copies, StandardInput.SOURCE_GRAPHIC))
