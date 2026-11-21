"""
Surface filters: grain, duotone and lighting (bevel, relief).
"""

from __future__ import annotations

from typing import Any

from ..color.color import Color, as_color
from ..elements import (
    ColorMatrixType,
    CompositeOperator,
    FeColorMatrix,
    FeComposite,
    FeDiffuseLighting,
    FeDistantLight,
    FeGaussianBlur,
    FeSpecularLighting,
    FeTurbulence,
    Filter,
    StandardInput,
    TurbulenceType,
)
from ..preset import filter
from ..theme import Theme
from ._constants import (
    ALPHA_ROW,
    GRAIN_AMOUNT,
    GRAIN_FREQUENCY,
    LIGHT_AZIMUTH,
    LIGHT_ELEVATION,
    LUMA,
    SPECULAR_CONSTANT,
    SPECULAR_EXPONENT,
    SURFACE_SCALE,
)
from ._parts import region

__all__ = ["bevel", "duotone", "grain", "relief"]


@filter
def grain(amount: float = GRAIN_AMOUNT, *, frequency: float = GRAIN_FREQUENCY, seed: int = 0,
          **kwargs: Any) -> Filter:
    """Film grain: grey fractal noise mixed into the element's colors, inside its shape.

    Parameters
    ----------
    amount : float, optional
        Strength of the noise, ``0..1``. Defaults to 0.25.
    frequency : float, optional
        Noise frequency; higher is finer. Defaults to 0.8.
    seed : int, optional
        Noise seed; equal seeds give equal grain. Defaults to 0.
    **kwargs
        Forwarded to :class:`~svgwriter.Filter`.

    Returns
    -------
    Filter
        The grain filter.

    See Also
    --------
    svgwriter.patterns.noise : Noise as a paint.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.filters.grain(seed=4).children[0].get("seed")
    4
    """
    noise = FeTurbulence(frequency, 2, seed=seed, type=TurbulenceType.FRACTAL_NOISE)
    grey = FeColorMatrix(ColorMatrixType.SATURATE, 0, in_=noise)
    mixed = FeComposite(CompositeOperator.ARITHMETIC, in_=StandardInput.SOURCE_GRAPHIC, in2=grey, k2=1, k3=amount,
                        k4=-amount / 2)
    inside = FeComposite(CompositeOperator.IN, in_=mixed, in2=StandardInput.SOURCE_ALPHA)
    return region(noise, grey, mixed, inside, margin="0%", extent="100%", **kwargs)


@filter
def duotone(dark: Color | str | None = None, light: Color | str | None = None, **kwargs: Any) -> Filter:
    """Recolor by brightness: shadows take *dark*, highlights *light*, the rest a blend of the two.

    Parameters
    ----------
    dark : Color or str, optional
        Color of black. Defaults to None, the current theme's primary color.
    light : Color or str, optional
        Color of white. Defaults to None, the current theme's accent color.
    **kwargs
        Forwarded to :class:`~svgwriter.Filter`.

    Returns
    -------
    Filter
        The duotone filter.

    Notes
    -----
    The colors are numbers in a color matrix, so theme defaults come from
    :meth:`Theme.current <svgwriter.Theme.current>` when the filter is built.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.filters.duotone("black", "white").children[0].get("values"))
    20
    """
    palette = Theme.current().palette
    low = as_color(dark if dark is not None else palette.primary)
    high = as_color(light if light is not None else palette.accent)
    rows: list[float] = []
    for start, stop in zip((low.r, low.g, low.b), (high.r, high.g, high.b), strict=True):
        rows += [(stop - start) * weight for weight in LUMA] + [0.0, start]
    return region(FeColorMatrix(ColorMatrixType.MATRIX, rows + list(ALPHA_ROW)), **kwargs)


def _lit(rim: FeGaussianBlur, light: FeDiffuseLighting | FeSpecularLighting, kwargs: dict[str, Any]) -> Filter:
    """*light* falling on the shape inside its outline: added to its colors (specular) or multiplying them."""
    inside = FeComposite(CompositeOperator.IN, in_=light, in2=StandardInput.SOURCE_ALPHA)
    weights = {"k2": 1, "k3": 1} if isinstance(light, FeSpecularLighting) else {"k1": 1}
    lit = FeComposite(CompositeOperator.ARITHMETIC, in_=StandardInput.SOURCE_GRAPHIC, in2=inside, **weights)
    return region(rim, light, inside, lit, **kwargs)


@filter
def bevel(depth: float = SURFACE_SCALE, *, azimuth: float = LIGHT_AZIMUTH, elevation: float = LIGHT_ELEVATION,
          shine: float = SPECULAR_EXPONENT, color: Color | str = "white", **kwargs: Any) -> Filter:
    """A glossy raised edge: a specular highlight on the rounded rim of the shape.

    Parameters
    ----------
    depth : float, optional
        Height of the rim (the surface scale). Defaults to 3.
    azimuth : float, optional
        Direction the light comes from, in degrees. Defaults to 225 (top left).
    elevation : float, optional
        Height of the light above the page, in degrees. Defaults to 45.
    shine : float, optional
        Specular exponent; higher is a tighter highlight. Defaults to 20.
    color : Color or str, optional
        Light color. Defaults to ``"white"``.
    **kwargs
        Forwarded to :class:`~svgwriter.Filter`.

    Returns
    -------
    Filter
        The bevel filter.

    See Also
    --------
    relief : Matte shading instead of a highlight.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.filters.bevel().children[1].tag
    'feSpecularLighting'
    """
    rim = FeGaussianBlur(depth / 2, in_=StandardInput.SOURCE_ALPHA)
    light = FeSpecularLighting(FeDistantLight(azimuth=azimuth, elevation=elevation), in_=rim, surface_scale=depth,
                               specular_constant=SPECULAR_CONSTANT, specular_exponent=shine, lighting_color=color)
    return _lit(rim, light, kwargs)


@filter
def relief(depth: float = SURFACE_SCALE, *, azimuth: float = LIGHT_AZIMUTH, elevation: float = LIGHT_ELEVATION,
           color: Color | str = "white", **kwargs: Any) -> Filter:
    """Matte shading of a raised shape lit from one side.

    Parameters
    ----------
    depth, azimuth, elevation, color, **kwargs
        As for :func:`bevel`.

    Returns
    -------
    Filter
        The relief filter.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.filters.relief().children[1].tag
    'feDiffuseLighting'
    """
    rim = FeGaussianBlur(depth / 2, in_=StandardInput.SOURCE_ALPHA)
    light = FeDiffuseLighting(FeDistantLight(azimuth=azimuth, elevation=elevation), in_=rim, surface_scale=depth,
                              diffuse_constant=1, lighting_color=color)
    return _lit(rim, light, kwargs)
