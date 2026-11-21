"""
The built-in gradients: theme, sunset, ocean, metallic, iridescent and mesh.
"""

from __future__ import annotations

from typing import Any

from ...model.color.color import Color, ColorLike, as_color
from ...model.elements import LinearGradient, Pattern, RadialGradient, Rect, Stop
from ...model.theme import Theme
from ..preset import gradient
from ._constants import (
    IRIDESCENT_CHROMA,
    IRIDESCENT_LIGHTNESS,
    IRIDESCENT_STEPS,
    MESH_CORNERS,
    MESH_REACH,
    METAL_BANDS,
    OCEAN,
    SPACE,
    SUNSET,
)
from ._stops import linear, palette_color, smooth_stops

__all__ = ["blend", "iridescent", "mesh", "metallic", "ocean", "sunset", "theme"]


@gradient
def theme(start: ColorLike | None = None, end: ColorLike | None = None, *, angle: float = 0.0,
          **kwargs: Any) -> LinearGradient:
    """The theme's primary color blending into its accent, sampled in OKLCH.

    Parameters
    ----------
    start, end : Color or str, optional
        End colors. Default to None, the current theme's primary and accent colors.
    angle : float, optional
        Direction in degrees: 0 runs left to right, 90 top to bottom. Defaults to 0.
    **kwargs
        Forwarded to :class:`~svgwriter.LinearGradient`.

    Returns
    -------
    LinearGradient
        A bounding-box gradient; ``fill=svg.gradients.theme()`` puts it into ``<defs>``.

    Notes
    -----
    Stop colors are numbers, so theme defaults come from :meth:`Theme.current <svgwriter.Theme.current>`
    when the gradient is built: build it inside ``with svg.Theme.get("dark"):`` for the dark palette.

    Examples
    --------
    >>> import svgwriter as svg
    >>> paint = svg.gradients.theme("navy", "gold", angle=90)
    >>> paint.get("y2"), len(paint.children)
    (1.0, 6)
    """
    palette = Theme.current().palette
    colors = (palette_color(start, palette.primary), palette_color(end, palette.accent))
    return linear(smooth_stops(colors), angle, **kwargs)


@gradient
def blend(*colors: ColorLike, angle: float = 0.0, **kwargs: Any) -> LinearGradient:
    """Any colors, evenly spaced and blended in OKLCH.

    Parameters
    ----------
    *colors : Color or str
        The colors, first to last. Defaults to the current theme's primary, secondary and accent colors.
    angle : float, optional
        Direction in degrees: 0 runs left to right, 90 top to bottom, -90 bottom to top. Defaults to 0.
    **kwargs
        Forwarded to :class:`~svgwriter.LinearGradient`.

    Returns
    -------
    LinearGradient
        The blended gradient.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.gradients.blend("red", "blue").children)
    6
    """
    if not colors:
        palette = Theme.current().palette
        colors = (palette.primary, palette.secondary, palette.accent)
    return linear(smooth_stops(colors), angle, **kwargs)


@gradient
def sunset(*, angle: float = 90.0, **kwargs: Any) -> LinearGradient:
    """Dusk violet through rose and orange to a pale gold horizon.

    Parameters
    ----------
    angle : float, optional
        Direction in degrees. Defaults to 90 (top to bottom).
    **kwargs
        Forwarded to :class:`~svgwriter.LinearGradient`.

    Returns
    -------
    LinearGradient
        The sunset gradient.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.gradients.sunset().children[0].get("stop-color").hex
    '#2b1055'
    """
    return linear(smooth_stops(SUNSET), angle, **kwargs)


@gradient
def ocean(*, angle: float = 90.0, **kwargs: Any) -> LinearGradient:
    """Sunlit shallows through turquoise to the deep.

    Parameters
    ----------
    angle : float, optional
        Direction in degrees. Defaults to 90 (top to bottom).
    **kwargs
        Forwarded to :class:`~svgwriter.LinearGradient`.

    Returns
    -------
    LinearGradient
        The ocean gradient.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.gradients.ocean().children)
    21
    """
    return linear(smooth_stops(OCEAN), angle, **kwargs)


@gradient
def metallic(base: ColorLike = "#a8adb5", *, angle: float = 90.0, **kwargs: Any) -> LinearGradient:
    """Brushed metal: bands of lighter and darker *base* with a sharp horizon line.

    Parameters
    ----------
    base : Color or str, optional
        Metal color: ``"#a8adb5"`` steel by default, ``"gold"`` or ``"#b87333"`` copper for others.
    angle : float, optional
        Direction in degrees. Defaults to 90 (top to bottom).
    **kwargs
        Forwarded to :class:`~svgwriter.LinearGradient`.

    Returns
    -------
    LinearGradient
        The metallic gradient.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.gradients.metallic("gold").children)
    6
    """
    color = as_color(base)
    stops = [Stop(offset, color.lighten(shift) if shift > 0 else color.darken(-shift)) for offset, shift in METAL_BANDS]
    return linear(stops, angle, **kwargs)


@gradient
def iridescent(hue: float = 200.0, *, sweep: float = 300.0, angle: float = 30.0, **kwargs: Any) -> LinearGradient:
    """A soap-film sheen: pale colors sweeping round the hue wheel at even lightness, in OKLCH.

    Parameters
    ----------
    hue : float, optional
        Starting OKLCH hue in degrees. Defaults to 200 (cyan).
    sweep : float, optional
        Degrees of hue covered. Defaults to 300.
    angle : float, optional
        Direction in degrees. Defaults to 30.
    **kwargs
        Forwarded to :class:`~svgwriter.LinearGradient`.

    Returns
    -------
    LinearGradient
        The iridescent gradient.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.gradients.iridescent().children)
    7
    """
    count = IRIDESCENT_STEPS
    colors = [Color.from_space(SPACE, (IRIDESCENT_LIGHTNESS, IRIDESCENT_CHROMA, hue + sweep * i / count))
              for i in range(count + 1)]
    return linear([Stop(round(i / count, 4), color) for i, color in enumerate(colors)], angle, **kwargs)


@gradient
def mesh(*corners: ColorLike, **kwargs: Any) -> Pattern:
    """A soft four-corner blend, like a gradient mesh: each corner's color fades out towards the others.

    The paint is a bounding-box pattern of radial gradients layered over the average color, so it
    stretches to any shape.

    Parameters
    ----------
    *corners : Color or str
        Up to four colors for the top-left, top-right, bottom-right and bottom-left corners. Defaults to
        the current theme's primary, secondary, accent and surface colors.
    **kwargs
        Forwarded to :class:`~svgwriter.Pattern`.

    Returns
    -------
    Pattern
        The mesh paint.

    Raises
    ------
    ValueError
        If more than four corners are given.

    Examples
    --------
    >>> import svgwriter as svg
    >>> paint = svg.gradients.mesh("red", "gold", "teal", "navy")
    >>> paint.tag, len(paint.children)
    ('pattern', 5)
    """
    if len(corners) > len(MESH_CORNERS):
        raise ValueError(f"mesh takes up to {len(MESH_CORNERS)} corner colors, not {len(corners)}")
    palette = Theme.current().palette
    defaults = (palette.primary, palette.secondary, palette.accent, palette.surface)
    colors = [as_color(c) for c in corners] + list(defaults[len(corners):])
    base = colors[0]
    for index, color in enumerate(colors[1:], start=2):
        base = base.mix(color, 1 / index, space=SPACE)
    layers = [Rect(0, 0, 1, 1, fill=base)]
    for (cx, cy), color in zip(MESH_CORNERS, colors, strict=True):
        glow = RadialGradient(Stop(0, color), Stop(1, color, 0), cx=cx, cy=cy, r=MESH_REACH)
        layers.append(Rect(0, 0, 1, 1, fill=glow))
    kwargs.setdefault("pattern_content_units", "objectBoundingBox")
    return Pattern(*layers, x=0, y=0, width=1, height=1, **kwargs)

