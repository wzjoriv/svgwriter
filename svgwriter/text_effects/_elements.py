"""
Text effects of the elements: fire, ice, smoke and snow.
"""

from __future__ import annotations

from ..gradients import blend
from ..model.elements import (
    Channel,
    ColorMatrixType,
    CompositeOperator,
    FeColorMatrix,
    FeComposite,
    FeDisplacementMap,
    FeDistantLight,
    FeGaussianBlur,
    FeMerge,
    FeOffset,
    FeSpecularLighting,
    FeTurbulence,
    StandardInput,
    Text,
    TurbulenceType,
)
from ..preset import text_effect
from ._constants import (
    FIRE_COLORS,
    FIRE_DURATION,
    FIRE_FREQUENCIES,
    FIRE_GLOW,
    FIRE_HEAT,
    ICE_COLORS,
    ICE_DURATION,
    ICE_FROST,
    ICE_GLINT,
    ICE_SWEEP,
    LIGHT_ELEVATION,
    SMOKE_COLOR,
    SMOKE_DURATION,
    SMOKE_FREQUENCIES,
    SMOKE_HAZE,
    SMOKE_SCALES,
    SMOKE_SOFTEN,
    SNOW_COLORS,
    SNOW_DENSITY,
    SNOW_DURATION,
    SNOW_FALL,
    SNOW_FLAKES,
    SNOW_GLOW,
    SNOW_RIM,
)
from ._parts import fit, loop, tinted

__all__ = ["fire", "ice", "smoke", "snow"]


@text_effect
def fire(text: Text, *, animate: bool = True, seed: int = 0) -> None:
    """Burning letters: a white-hot to ember gradient, licked upwards by flickering noise, with an orange glow.

    Parameters
    ----------
    text : Text
        The text, or (through the registered effect) a range such as ``text[4:9]``.
    animate : bool, optional
        Let the flames flicker (an SMIL loop, so it plays in browsers, GIFs and videos). Defaults to True.
    seed : int, optional
        Noise seed; other seeds give other flames. Defaults to 0.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(240, 60)
    >>> line = doc.text("carried sparks", x=10, y=40, font_size=28)
    >>> layer = svg.text_effects.fire(line[8:14])
    >>> layer.get("filter").element[0].children[0].get("attributeName")
    'baseFrequency'
    """
    size = fit(text)
    text.fill = blend(*FIRE_COLORS, angle=-90)
    noise = FeTurbulence(size.frequency(FIRE_FREQUENCIES[0]), 2, seed=seed)
    if animate:
        loop(noise, "baseFrequency", size.values(FIRE_FREQUENCIES), FIRE_DURATION)
    flames = FeDisplacementMap(size(FIRE_HEAT), Channel.R, Channel.G, in_=StandardInput.SOURCE_GRAPHIC, in2=noise)
    color, radius = FIRE_GLOW
    halo = FeGaussianBlur(size(radius), in_=flames)
    flood, glow = tinted(color, halo)
    text.filter = size.filter(noise, flames, halo, flood, glow, FeMerge(glow, flames))


@text_effect
def ice(text: Text, *, animate: bool = True) -> None:
    """Frozen letters: frost-white to glacier-blue, a cold halo and a glint that travels round the edges.

    Parameters
    ----------
    text : Text
        The text, or a range of it.
    animate : bool, optional
        Move the light round so the glint travels. Defaults to True.

    Examples
    --------
    >>> import svgwriter as svg
    >>> title = svg.text("cold", x=0, y=30, font_size=30)
    >>> svg.text_effects.ice(title, animate=False).get("filter").element[-1].tag
    'feMerge'
    """
    size = fit(text)
    text.fill = blend(*ICE_COLORS, angle=90)
    frost_color, frost_radius = ICE_FROST
    frost_blur = FeGaussianBlur(size(frost_radius), in_=StandardInput.SOURCE_ALPHA)
    flood, frost = tinted(frost_color, frost_blur)
    depth, shine, exponent = ICE_GLINT
    light = FeDistantLight(azimuth=ICE_SWEEP[0], elevation=LIGHT_ELEVATION)
    if animate:
        loop(light, "azimuth", size.values(ICE_SWEEP, frequency=True), ICE_DURATION)
    rim = FeGaussianBlur(size(depth), in_=StandardInput.SOURCE_ALPHA)
    glint = FeSpecularLighting(light, in_=rim, surface_scale=size(depth), specular_constant=shine,
                               specular_exponent=exponent, lighting_color="white")
    inside = FeComposite(CompositeOperator.IN, in_=glint, in2=StandardInput.SOURCE_ALPHA)
    lit = FeComposite(CompositeOperator.ARITHMETIC, in_=StandardInput.SOURCE_GRAPHIC, in2=inside, k2=1, k3=1)
    text.filter = size.filter(frost_blur, flood, frost, rim, glint, inside, lit, FeMerge(frost, lit))


@text_effect
def smoke(text: Text, *, animate: bool = True, seed: int = 0) -> None:
    """Smoky letters: soft grey glyphs that curl and drift inside a faint haze.

    Parameters
    ----------
    text : Text
        The text, or a range of it.
    animate : bool, optional
        Let the smoke curl. Defaults to True.
    seed : int, optional
        Noise seed. Defaults to 0.

    Examples
    --------
    >>> import svgwriter as svg
    >>> title = svg.text("Smoke", x=0, y=30, font_size=30)
    >>> svg.text_effects.smoke(title).fill.hex
    '#8d939b'
    """
    size = fit(text)
    text.fill = SMOKE_COLOR
    noise = FeTurbulence(size.frequency(SMOKE_FREQUENCIES[0]), 3, seed=seed, type=TurbulenceType.FRACTAL_NOISE)
    curl = FeDisplacementMap(size(SMOKE_SCALES[0]), Channel.R, Channel.G, in_=StandardInput.SOURCE_GRAPHIC,
                             in2=noise)
    if animate:
        loop(noise, "baseFrequency", size.values(SMOKE_FREQUENCIES), SMOKE_DURATION)
        loop(curl, "scale", size.values(SMOKE_SCALES), SMOKE_DURATION)
    soft = FeGaussianBlur(size(SMOKE_SOFTEN), in_=curl)
    radius, opacity = SMOKE_HAZE
    haze_blur = FeGaussianBlur(size(radius), in_=curl)
    flood, haze = tinted(SMOKE_COLOR, haze_blur, opacity)
    text.filter = size.filter(noise, curl, soft, haze_blur, flood, haze, FeMerge(haze, soft))


@text_effect
def snow(text: Text, *, animate: bool = True, seed: int = 0) -> None:
    """Snowy letters: white glyphs with a cold rim, flakes drifting down around them.

    Parameters
    ----------
    text : Text
        The text, or a range of it.
    animate : bool, optional
        Let the flakes fall. Defaults to True.
    seed : int, optional
        Seed of the flakes. Defaults to 0.

    Examples
    --------
    >>> import svgwriter as svg
    >>> title = svg.text("Snow", x=0, y=30, font_size=30)
    >>> svg.text_effects.snow(title, animate=False).stroke.hex
    '#bcd4ea'
    """
    size = fit(text)
    text.fill = blend(*SNOW_COLORS, angle=90)
    text.stroke = SNOW_COLORS[-1]
    text.stroke_width = size(SNOW_RIM)
    frequency, contrast = SNOW_FLAKES
    noise = FeTurbulence(round(frequency / size.scale, 4), 1, seed=seed, type=TurbulenceType.FRACTAL_NOISE)
    rows = [0.0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, contrast, 0, 0, 0, SNOW_DENSITY]
    flakes = FeColorMatrix(ColorMatrixType.MATRIX, rows, in_=noise)
    falling = FeOffset(0, 0, in_=flakes)
    if animate:
        loop(falling, "dy", size.values((0.0, SNOW_FALL)), SNOW_DURATION)
    radius, opacity = SNOW_GLOW
    glow_blur = FeGaussianBlur(size(radius), in_=StandardInput.SOURCE_ALPHA)
    flood, glow = tinted("white", glow_blur, opacity)
    text.filter = size.filter(noise, flakes, falling, glow_blur, flood, glow,
                              FeMerge(glow, StandardInput.SOURCE_GRAPHIC, falling))
