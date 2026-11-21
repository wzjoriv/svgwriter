"""
Rasterizing with skia: SVG text, documents and element trees into RGBA arrays.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Final

import numpy as np
import skia

from .._internal._render._rendering import view_matrix
from ..attributes.length import Length, Unit
from ..attributes.viewbox import ViewBox
from ._canvas import make_surface, paint_svg, read_pixels
from ._constants import CHANNEL_MAX, DEFAULT_QUALITY, FORMATS
from ._painting import paint_tree, render_tree

if TYPE_CHECKING:
    from ..color.color import ColorLike
    from ..document import Document

__all__ = [
    "DEFAULT_SIZE",
    "document_size",
    "page_size",
    "encode",
    "encode_image",
    "paint_tree",
    "rasterize",
    "render_png",
    "render_svg",
    "render_tree",
    "render_frame",
]

DEFAULT_SIZE: Final = 300.0


def _dimension(value: object, fallback: float) -> float:
    if value is None:
        return fallback
    length = Length.parse(value)
    return fallback if length.unit is Unit.PERCENT else length.to_user_units()


def document_size(document: Document) -> tuple[float, float]:
    """Canvas size in user units: ``width``/``height``, else the ``viewBox`` size, else 300.

    Percentages resolve against the ``viewBox`` (or 300) since there is no
    surrounding viewport. Sizes are rounded up to whole units.

    Parameters
    ----------
    document : Document
        The document to measure.

    Returns
    -------
    (float, float)
        Width and height in user units.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.render import document_size
    >>> document_size(svg.Document(40, 20))
    (40.0, 20.0)
    """
    width, height = page_size(document)
    return float(max(1, math.ceil(width))), float(max(1, math.ceil(height)))


def page_size(document: Document) -> tuple[float, float]:
    """Exact page size in user units (CSS pixels, 96 per inch): ``width``/``height``, else the ``viewBox`` size, else 300.

    Unlike :func:`document_size` the size is not rounded, so vector formats keep the physical
    size: a ``210mm`` wide document is 793.7 user units, 595.28 points.

    Parameters
    ----------
    document : Document
        The document to measure.

    Returns
    -------
    (float, float)
        Width and height in user units.

    See Also
    --------
    document_size : The size rounded up to whole pixels for rasters.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.render import page_size
    >>> [round(v, 2) for v in page_size(svg.Document(210 * svg.mm, 297 * svg.mm))]
    [793.7, 1122.52]
    """
    root = document.root
    box = root.view_box
    return (_dimension(root.get("width"), box.width if box else DEFAULT_SIZE),
            _dimension(root.get("height"), box.height if box else DEFAULT_SIZE))


def render_svg(
    text: str, width: float, height: float, *, scale: float = 1.0, background: ColorLike | None = None
) -> np.ndarray:
    """Render SVG *text* at ``width x height`` user units into an RGBA array.

    Parameters
    ----------
    text : str
        A complete SVG document.
    width, height : float
        Size in user units; the pixel size is this times *scale*, rounded up.
    scale : float, optional
        Pixels per user unit. Defaults to 1.0.
    background : color, optional
        Painted under the drawing; transparent when omitted. Defaults to None.

    Returns
    -------
    numpy.ndarray
        ``float32`` array of shape ``(rows, columns, 4)``, straight (not
        premultiplied) RGBA in ``0..1``.

    Raises
    ------
    ValueError
        If skia cannot parse the document.

    See Also
    --------
    rasterize : Render a :class:`~svgwriter.Document`, embedded images included.

    Notes
    -----
    Skia's SVG renderer does not load ``<image>`` content; :func:`render_tree`
    and :func:`rasterize` draw embedded images.

    Examples
    --------
    >>> from svgwriter.ops import render_svg
    >>> text = (
    ...     '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="2">'
    ...     '<rect width="4" height="2" fill="red"/></svg>'
    ... )
    >>> pixels = render_svg(text, 4, 2)
    >>> pixels.shape
    (2, 4, 4)
    >>> pixels[0, 0].tolist()
    [1.0, 0.0, 0.0, 1.0]
    """
    surface = make_surface(width, height, scale, background)
    paint_svg(surface.getCanvas(), text, width, height)
    return read_pixels(surface)


def rasterize(
    document: Document,
    *,
    scale: float = 1.0,
    size: tuple[int, int] | int | None = None,
    padding: float = 0.0,
    background: ColorLike | None = None,
    snapshot: bool = False,
) -> Any:
    """Render *document* into an RGBA array, embedded images included.

    Parameters
    ----------
    document : Document
        What to draw; SMIL animation is not evaluated.
    scale : float, optional
        Pixels per user unit of the document's size (see :func:`document_size`). Defaults to 1.0.
    size : (int, int) or int, optional
        Exact output ``(columns, rows)``, or one int for a square; a ``viewBox`` drawing is fitted
        into it and *scale* is ignored. Without a ``viewBox`` this is the
        viewport size in user units. Defaults to None.
    padding : float, optional
        Margin around the drawing in its own (``viewBox``) units; with
        *size* the padded drawing is fitted and centred. Defaults to 0.0.
    background : color, optional
        Painted under the drawing; transparent when omitted. Defaults to None.
    snapshot : bool, optional
        Return a ``skia.Image`` instead (no conversion; for encoding). Defaults to False.

    Returns
    -------
    numpy.ndarray or skia.Image
        ``float32`` ``(rows, columns, 4)`` straight RGBA in ``0..1``, or the image when
        *snapshot* is true.

    See Also
    --------
    render_png : Render straight to PNG bytes.

    Notes
    -----
    Output is deterministic: the same document gives the same pixels.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(4, 2)
    >>> _ = doc.rect(0, 0, 4, 2, fill="red")
    >>> rasterize(doc).shape
    (2, 4, 4)
    >>> rasterize(doc, size=(32, 32), padding=1).shape
    (32, 32, 4)
    """
    width, height = document_size(document)
    box = document.root.view_box
    padded = None
    if padding:
        base = box or ViewBox(0.0, 0.0, width, height)
        unit = width / base.width if base.width else 1.0
        padded = ViewBox(base.min_x - padding, base.min_y - padding, base.width + 2 * padding,
                         base.height + 2 * padding)
        box, width, height = padded, padded.width * unit, padded.height * unit
    if isinstance(size, int):
        size = (size, size)
    if size is not None:
        columns, rows = size
        if box is None:
            width, height, scale = float(columns), float(rows), 1.0
        else:
            scale = min(columns / width, rows / height)
            width, height = columns / scale, rows / scale
    return render_tree(document.root, lambda text: text, width, height, view=view_matrix(document, width, height, box),
                       scale=scale, background=background, viewport=True, view_box=padded, snapshot=snapshot)


def encode_image(image: Any, format: str = "png", *, quality: int = DEFAULT_QUALITY) -> bytes:
    """Encode a ``skia.Image`` as PNG, JPEG or WebP bytes.

    Parameters
    ----------
    image : skia.Image
        The image to encode.
    format : {"png", "jpeg", "jpg", "webp"}, optional
        Output format, case-insensitive. Defaults to "png".
    quality : int, optional
        Compression quality for lossy formats, 0 to 100. Defaults to 90.

    Returns
    -------
    bytes
        The encoded file.

    Raises
    ------
    ValueError
        If *format* is unknown or skia cannot encode the image.

    See Also
    --------
    encode : Encode an RGBA array instead.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.render import encode_image, rasterize
    >>> doc = svg.Document(4, 4)
    >>> encode_image(rasterize(doc, snapshot=True), "jpeg")[:2] == bytes.fromhex("ffd8")
    True
    """
    try:
        kind = FORMATS[format.lower()]
    except KeyError:
        raise ValueError(f"unknown image format {format!r}; expected one of {sorted(FORMATS)}") from None
    data = image.encodeToData(kind, quality)
    if data is None:
        raise ValueError(f"skia could not encode {format}")
    return bytes(data)


def encode(pixels: np.ndarray, format: str = "png", *, quality: int = DEFAULT_QUALITY) -> bytes:
    """Encode an RGBA array (floats in ``0..1`` or ``uint8``) as PNG, JPEG or WebP bytes.

    Parameters
    ----------
    pixels : numpy.ndarray
        Straight RGBA array of shape ``(rows, columns, 4)``; floats are scaled from ``0..1``.
    format : {"png", "jpeg", "jpg", "webp"}, optional
        Output format, case-insensitive. Defaults to "png".
    quality : int, optional
        Compression quality for lossy formats, 0 to 100. Defaults to 90.

    Returns
    -------
    bytes
        The encoded file.

    Raises
    ------
    ValueError
        If *format* is unknown or skia cannot encode the image.

    See Also
    --------
    encode_image : Encode a ``skia.Image`` without converting it.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter.ops import encode
    >>> encode(np.ones((1, 1, 4)))[:4] == bytes.fromhex("89504e47")
    True
    """
    if format.lower() not in FORMATS:
        raise ValueError(f"unknown image format {format!r}; expected one of {sorted(FORMATS)}")
    array = np.asarray(pixels)
    if array.dtype != np.uint8:
        array = np.clip(np.rint(array * CHANNEL_MAX), 0, CHANNEL_MAX).astype(np.uint8)
    array = np.ascontiguousarray(array)
    image = skia.Image.fromarray(array, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return encode_image(image, format, quality=quality)


def render_png(document: Document, *, scale: float = 1.0, background: ColorLike | None = None) -> bytes:
    """Render *document* to PNG bytes.

    Parameters
    ----------
    document : Document
        What to draw.
    scale : float, optional
        Pixels per user unit. Defaults to 1.0.
    background : color, optional
        Painted under the drawing; transparent when omitted. Defaults to None.

    Returns
    -------
    bytes
        The PNG file.

    See Also
    --------
    rasterize : Get the pixels as an array.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import render_png
    >>> render_png(svg.Document(4, 4))[:4] == bytes.fromhex("89504e47")
    True
    """
    return encode_image(rasterize(document, scale=scale, background=background, snapshot=True))


def render_frame(document: Document, time: float) -> np.ndarray:
    """Frame renderer for :func:`~svgwriter.video.render_animation`: an opaque uint8 RGBA frame.

    Draws the document as it is at each frame (use ``update=`` to change it
    over time) on white, and returns raw pixels so ffmpeg needs no PNG
    decoding.

    Parameters
    ----------
    document : Document
        The document to draw.
    time : float
        The frame time; unused, since the document itself carries the state.

    Returns
    -------
    numpy.ndarray
        ``uint8`` array of shape ``(rows, columns, 4)``.

    Raises
    ------
    ValueError
        If skia cannot read the rendered pixels.

    See Also
    --------
    rasterize : Render with transparency and float output.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import render_frame
    >>> frame = render_frame(svg.Document(4, 2), 0.0)
    >>> frame.shape, frame.dtype.name
    ((2, 4, 4), 'uint8')
    """
    from .._internal._smil import snapshot
    from ..elements.animation import AnimationElement

    if document.root.find(AnimationElement) is not None:
        document = snapshot(document, time)
    image = document.rasterize(background="white", snapshot=True)
    info = skia.ImageInfo.Make(image.width(), image.height(), skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    frame = np.empty((image.height(), image.width(), 4), np.uint8)
    if not image.readPixels(info, frame, info.minRowBytes()):
        raise ValueError("skia could not read the frame")
    return frame
