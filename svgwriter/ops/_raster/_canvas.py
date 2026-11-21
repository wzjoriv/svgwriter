"""
Skia surfaces for rasterizing: creation, SVG painting and pixel read-back.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import skia

from .._constants import CHANNEL_MAX, PIXEL_EPSILON

if TYPE_CHECKING:
    from ...color.color import ColorLike

__all__ = ["make_surface", "paint_svg", "read_pixels"]


def _pixels_for(extent: float) -> int:
    """Pixel count covering *extent*, ignoring float round-off just above an integer."""
    return max(1, math.ceil(extent - PIXEL_EPSILON))


def make_surface(width: float, height: float, scale: float, background: ColorLike | None) -> skia.Surface:
    """A raster surface of the scaled size, cleared to *background* and scaled to user units."""
    from ...color.color import as_color

    surface = skia.Surface(_pixels_for(width * scale), _pixels_for(height * scale))
    if background is not None:
        r, g, b, a = as_color(background).uint8
        surface.getCanvas().clear(skia.Color(r, g, b, a))
    surface.getCanvas().scale(scale, scale)
    return surface


def paint_svg(canvas: skia.Canvas, text: str, width: float, height: float) -> None:
    """Draw SVG *text* onto *canvas* with skia's SVG renderer."""
    data = text.encode("utf-8")
    dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(data, True))
    if dom is None:
        raise ValueError("skia could not parse the document")
    dom.setContainerSize(skia.Size(width, height))
    dom.render(canvas)


def read_pixels(surface: skia.Surface) -> np.ndarray:
    """The surface as straight RGBA floats in ``0..1``."""
    image = surface.makeImageSnapshot()
    pixels = image.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return pixels.astype(np.float32) / CHANNEL_MAX
