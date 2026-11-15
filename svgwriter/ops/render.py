"""Rasterizing with skia: SVG text, documents and element trees into RGBA arrays."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, Final

import numpy as np
import skia

from ..attributes.length import Length
from ..transform.matrix import IDENTITY, Matrix
from ._layers import draw_image, hidden, layers

if TYPE_CHECKING:
    from ..document import Document
    from ..elements.base import Element

__all__ = ["DEFAULT_SIZE", "encode", "rasterize", "render_png", "render_svg", "render_tree", "skia_renderer"]

DEFAULT_SIZE: Final = 300.0
DEFAULT_QUALITY: Final = 90
CHANNEL_MAX: Final = 255
DISPLAY: Final = "display"


def _size(document: Document) -> tuple[float, float]:
    root = document.root
    box = root.view_box
    width, height = root.get("width"), root.get("height")
    w = Length.parse(width).to_user_units() if width is not None else (box.width if box else DEFAULT_SIZE)
    h = Length.parse(height).to_user_units() if height is not None else (box.height if box else DEFAULT_SIZE)
    return float(max(1, math.ceil(w))), float(max(1, math.ceil(h)))


def _surface(width: float, height: float, scale: float, background: str | None) -> skia.Surface:
    from ..color.color import as_color

    surface = skia.Surface(max(1, math.ceil(width * scale)), max(1, math.ceil(height * scale)))
    if background is not None:
        r, g, b, a = as_color(background).uint8
        surface.getCanvas().clear(skia.Color(r, g, b, a))
    surface.getCanvas().scale(scale, scale)
    return surface


def _paint_svg(canvas: skia.Canvas, text: str, width: float, height: float) -> None:
    data = text.encode("utf-8")
    dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(data, True))
    if dom is None:
        raise ValueError("skia could not parse the document")
    dom.setContainerSize(skia.Size(width, height))
    dom.render(canvas)


def _pixels(surface: skia.Surface) -> np.ndarray:
    image = surface.makeImageSnapshot()
    pixels = image.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return pixels.astype(np.float32) / CHANNEL_MAX


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

    Notes
    -----
    Text is drawn by skia's SVG renderer, which does not load ``<image>``
    content; :func:`render_tree` and :func:`rasterize` draw embedded images.
    """
    surface = _surface(width, height, scale, background)
    _paint_svg(surface.getCanvas(), text, width, height)
    return _pixels(surface)


def render_tree(
    root: Element,
    wrap: Callable[[str], str],
    width: float,
    height: float,
    *,
    view: Matrix = IDENTITY,
    scale: float = 1.0,
    background: str | None = None,
) -> np.ndarray:
    """Render the tree under *root*, drawing embedded ``<image>`` pixels in paint order.

    Parameters
    ----------
    root : Element
        A root ``<svg>`` or any element.
    wrap : callable
        Turns the serialized *root* into a complete SVG document.
    width, height : float
        Canvas size in user units.
    view : Matrix
        Maps *root*'s parent coordinates to canvas user units (the ``viewBox`` mapping).
    scale : float
        Pixels per user unit.
    background : color, optional
        Painted under the drawing.

    Returns
    -------
    numpy.ndarray
        ``float32`` ``(rows, columns, 4)`` straight RGBA in ``0..1``.
    """
    from ..io.writer import to_string

    surface = _surface(width, height, scale, background)
    canvas = surface.getCanvas()
    root = renderable_copy(root)
    parts = layers(root)
    for run, image in parts:
        if run or len(parts) == 1:
            for leaf in hidden(root, run) if len(parts) > 1 else ():
                leaf.attributes[DISPLAY] = "none"
            _paint_svg(canvas, wrap(to_string(root, xml_declaration=False, pretty=False)), width, height)
            for leaf in hidden(root, run) if len(parts) > 1 else ():
                leaf.attributes.pop(DISPLAY, None)
        if image is not None:
            draw_image(canvas, image, root, view)
    return _pixels(surface)


def renderable_copy(root: Element) -> Element:
    """A copy of *root* with every ``<text>`` replaced by its glyph outlines.

    skia's SVG renderer draws no text, so text is drawn as paths.
    """
    from ..elements.text import Text

    copy = root.copy()
    if isinstance(copy, Text):
        return copy.to_path(id=copy.id)
    for text in [e for e in copy.iter() if isinstance(e, Text)]:
        parent = text.parent
        assert parent is not None
        index = parent.children.index(text)
        parent.remove(text)
        parent.insert(index, text.to_path(id=text.id))
    return copy


def _view(document: Document, width: float, height: float) -> Matrix:
    box = document.root.view_box
    if box is None or not box.width or not box.height:
        return IDENTITY
    s = min(width / box.width, height / box.height)
    return (Matrix.translate((width - box.width * s) / 2, (height - box.height * s) / 2)
            @ Matrix.scale(s) @ Matrix.translate(-box.min_x, -box.min_y))


def rasterize(document: Document, *, scale: float = 1.0, background: str | None = None) -> np.ndarray:
    """Render *document* into an RGBA array, embedded images included.

    Parameters
    ----------
    document : Document
        What to draw; SMIL animation is not evaluated.
    scale : float
        Pixels per user unit of the document's ``width``/``height``.
    background : color, optional
        Painted under the drawing; transparent when omitted.

    Returns
    -------
    numpy.ndarray
        ``float32`` ``(rows, columns, 4)`` straight RGBA in ``0..1``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(4, 2)
    >>> _ = doc.rect(0, 0, 4, 2, fill="red")
    >>> rasterize(doc).shape
    (2, 4, 4)
    """
    width, height = _size(document)
    return render_tree(document.root, lambda text: text, width, height, view=_view(document, width, height),
                       scale=scale, background=background)


def encode(pixels: np.ndarray, format: str = "png", *, quality: int = DEFAULT_QUALITY) -> bytes:
    """Encode an RGBA array (floats in ``0..1`` or ``uint8``) as PNG, JPEG or WebP bytes.

    Examples
    --------
    >>> encode(np.ones((1, 1, 4)))[:4] == bytes.fromhex("89504e47")
    True
    """
    formats = {"png": skia.kPNG, "jpeg": skia.kJPEG, "jpg": skia.kJPEG, "webp": skia.kWEBP}
    try:
        kind = formats[format.lower()]
    except KeyError:
        raise ValueError(f"unknown image format {format!r}; expected one of {sorted(formats)}") from None
    array = np.asarray(pixels)
    if array.dtype != np.uint8:
        array = np.clip(np.rint(array * CHANNEL_MAX), 0, CHANNEL_MAX).astype(np.uint8)
    array = np.ascontiguousarray(array)
    image = skia.Image.fromarray(array, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    data = image.encodeToData(kind, quality)
    if data is None:
        raise ValueError(f"skia could not encode {format}")
    return bytes(data)


def render_png(document: Document, *, scale: float = 1.0, background: str | None = None) -> bytes:
    """Render *document* to PNG bytes."""
    return encode(rasterize(document, scale=scale, background=background))


def skia_renderer(document: Document, time: float) -> bytes:
    """Frame renderer for :func:`~svgwriter.video.render_animation`.

    Draws the document as it is at each frame; use ``update=`` to change
    it over time.
    """
    del time
    return render_png(document, background="white")
