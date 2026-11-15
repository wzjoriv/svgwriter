"""Rasterizing documents with skia's SVG renderer."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Final

import numpy as np
import skia

from ..attributes.length import Length

if TYPE_CHECKING:
    from ..document import Document

__all__ = ["DEFAULT_SIZE", "encode", "rasterize", "render_png", "render_svg", "skia_renderer"]

DEFAULT_SIZE: Final = 300.0
DEFAULT_QUALITY: Final = 90
CHANNEL_MAX: Final = 255


def _size(document: Document) -> tuple[int, int]:
    root = document.root
    box = root.view_box
    width, height = root.get("width"), root.get("height")
    w = Length.parse(width).to_user_units() if width is not None else (box.width if box else DEFAULT_SIZE)
    h = Length.parse(height).to_user_units() if height is not None else (box.height if box else DEFAULT_SIZE)
    return max(1, math.ceil(w)), max(1, math.ceil(h))


def render_svg(
    text: str, width: float, height: float, *, scale: float = 1.0, background: str | None = None
) -> np.ndarray:
    """Render SVG *text* at ``width x height`` user units into an RGBA array.

    Parameters
    ----------
    text : str
        A complete SVG document.
    width, height : float
        Size in user units; the pixel size is this times *scale*, rounded up.
    scale : float
        Pixels per user unit.
    background : color, optional
        Painted under the drawing; transparent when omitted.

    Returns
    -------
    numpy.ndarray
        ``float32`` array of shape ``(rows, columns, 4)``, straight (not
        premultiplied) RGBA in ``0..1``.
    """
    from ..color.color import as_color

    data = text.encode("utf-8")
    dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(data, True))
    if dom is None:
        raise ValueError("skia could not parse the document")
    columns, rows = max(1, math.ceil(width * scale)), max(1, math.ceil(height * scale))
    surface = skia.Surface(columns, rows)
    with surface as canvas:
        if background is not None:
            r, g, b, a = as_color(background).uint8
            canvas.clear(skia.Color(r, g, b, a))
        canvas.scale(scale, scale)
        dom.setContainerSize(skia.Size(width, height))
        dom.render(canvas)
    image = surface.makeImageSnapshot()
    pixels = image.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return pixels.astype(np.float32) / CHANNEL_MAX


def rasterize(document: Document, *, scale: float = 1.0, background: str | None = None) -> np.ndarray:
    """Render *document* into an RGBA array (see :func:`render_svg`).

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(4, 2)
    >>> _ = doc.rect(0, 0, 4, 2, fill="red")
    >>> rasterize(doc).shape
    (2, 4, 4)
    """
    width, height = _size(document)
    return render_svg(document.to_string(), width, height, scale=scale, background=background)


def encode(pixels: np.ndarray, format: str = "png", *, quality: int = DEFAULT_QUALITY) -> bytes:
    """Encode an RGBA array (floats in ``0..1`` or ``uint8``) as PNG, JPEG or WebP bytes."""
    formats = {"png": skia.kPNG, "jpeg": skia.kJPEG, "jpg": skia.kJPEG, "webp": skia.kWEBP}
    try:
        kind = formats[format.lower()]
    except KeyError:
        raise ValueError(f"unknown image format {format!r}; expected one of {sorted(formats)}") from None
    array = np.asarray(pixels)
    if array.dtype != np.uint8:
        array = np.clip(np.rint(array * CHANNEL_MAX), 0, CHANNEL_MAX).astype(np.uint8)
    image = skia.Image.fromarray(np.ascontiguousarray(array), colorType=skia.kRGBA_8888_ColorType,
                                 alphaType=skia.kUnpremul_AlphaType)
    data = image.encodeToData(kind, quality)
    if data is None:
        raise ValueError(f"skia could not encode {format}")
    return bytes(data)


def render_png(document: Document, *, scale: float = 1.0, background: str | None = None) -> bytes:
    """Render *document* to PNG bytes."""
    return encode(rasterize(document, scale=scale, background=background))


def skia_renderer(document: Document, time: float) -> bytes:
    """Frame renderer for :func:`~svgwriter.animate.render_animation`.

    Draws the document as it is at each frame; use ``update=`` to change
    it over time.
    """
    del time
    return render_png(document, background="white")
