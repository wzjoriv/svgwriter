"""
Rasterizing with skia: SVG text, documents and element trees into RGBA arrays.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final

import numpy as np
import skia

from ..attributes.length import Length, Unit
from ..attributes.viewbox import ViewBox
from ..transform.matrix import IDENTITY, Matrix
from ._layers import draw_image, hidden, layers, resolve_links

if TYPE_CHECKING:
    from ..color.color import ColorLike
    from ..document import Document
    from ..elements.base import Element
    from ..elements.text import Text

__all__ = [
    "DEFAULT_SIZE",
    "document_size",
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
DEFAULT_QUALITY: Final = 90
CHANNEL_MAX: Final = 255
DISPLAY: Final = "display"
PIXEL_EPSILON: Final = 1e-6
FORMATS: Final = {"png": skia.kPNG, "jpeg": skia.kJPEG, "jpg": skia.kJPEG, "webp": skia.kWEBP}


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
    root = document.root
    box = root.view_box
    w = _dimension(root.get("width"), box.width if box else DEFAULT_SIZE)
    h = _dimension(root.get("height"), box.height if box else DEFAULT_SIZE)
    return float(max(1, math.ceil(w))), float(max(1, math.ceil(h)))


def _pixels_for(extent: float) -> int:
    """Pixel count covering *extent*, ignoring float round-off just above an integer."""
    return max(1, math.ceil(extent - PIXEL_EPSILON))


def _surface(width: float, height: float, scale: float, background: ColorLike | None) -> skia.Surface:
    from ..color.color import as_color

    surface = skia.Surface(_pixels_for(width * scale), _pixels_for(height * scale))
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
    background: ColorLike | None = None,
    viewport: bool = False,
    view_box: ViewBox | None = None,
    snapshot: bool = False,
) -> Any:
    """Render the tree under *root*, drawing embedded ``<image>`` pixels in paint order.

    Parameters
    ----------
    root : Element
        A root ``<svg>`` or any element.
    wrap : callable
        Turns the serialized *root* into a complete SVG document.
    width, height : float
        Canvas size in user units.
    view : Matrix, optional
        Maps *root*'s parent coordinates to canvas user units (the ``viewBox`` mapping).
        Defaults to the identity.
    scale : float, optional
        Pixels per user unit. Defaults to 1.0.
    background : color, optional
        Painted under the drawing. Defaults to None.
    viewport : bool, optional
        *root* is the outermost ``<svg>``: draw it at exactly ``width x height``. Defaults to False.
    view_box : ViewBox, optional
        Replace the root's ``viewBox`` while drawing (used for padding). Defaults to None.
    snapshot : bool, optional
        Return the ``skia.Image`` instead of an array (encoders use it directly). Defaults to False.

    Returns
    -------
    numpy.ndarray or skia.Image
        ``float32`` ``(rows, columns, 4)`` straight RGBA in ``0..1``, or the image when
        *snapshot* is true.

    See Also
    --------
    rasterize : Render a whole document.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.render import render_tree
    >>> doc = svg.Document(4, 2)
    >>> _ = doc.rect(0, 0, 4, 2, fill="red")
    >>> render_tree(doc.root, lambda text: text, 4, 2, viewport=True).shape
    (2, 4, 4)
    """
    surface = _surface(width, height, scale, background)
    paint_tree(surface.getCanvas(), root, wrap, width, height, view=view, viewport=viewport, view_box=view_box)
    return surface.makeImageSnapshot() if snapshot else _pixels(surface)


def paint_tree(
    canvas: skia.Canvas,
    root: Element,
    wrap: Callable[[str], str],
    width: float,
    height: float,
    *,
    view: Matrix = IDENTITY,
    viewport: bool = False,
    view_box: ViewBox | None = None,
    native_text: bool = False,
) -> None:
    """Paint the tree under *root* onto any skia canvas (raster, PDF, ...).

    Text becomes outlines (or real glyphs with *native_text*) and embedded images are drawn in
    paint order; the other arguments match :func:`render_tree`.

    Parameters
    ----------
    canvas : skia.Canvas
        Destination canvas.
    root : Element
        A root ``<svg>`` or any element.
    wrap : callable
        Turns the serialized *root* into a complete SVG document.
    width, height : float
        Canvas size in user units.
    view : Matrix, optional
        Maps *root*'s parent coordinates to canvas user units. Defaults to the identity.
    viewport : bool, optional
        *root* is the outermost ``<svg>``: draw it at exactly ``width x height``. Defaults to False.
    view_box : ViewBox, optional
        Replace the root's ``viewBox`` while drawing. Defaults to None.
    native_text : bool, optional
        Draw text that a canvas can reproduce exactly (plain colours, no filter or mask) as real
        glyphs, so a PDF canvas keeps it selectable. Defaults to False.

    See Also
    --------
    render_tree : Paint onto a new raster surface and return the pixels.

    Examples
    --------
    >>> import skia
    >>> import svgwriter as svg
    >>> from svgwriter.ops.render import paint_tree
    >>> doc = svg.Document(4, 2)
    >>> _ = doc.rect(0, 0, 4, 2, fill="red")
    >>> surface = skia.Surface(4, 2)
    >>> paint_tree(surface.getCanvas(), doc.root, lambda text: text, 4, 2, viewport=True)
    """
    from ..elements.text import Text
    from ..io.writer import to_string
    from ._native_text import draw_text
    from ._native_text import native_text as drawable

    root = renderable_copy(root, keep_text=drawable if native_text else None)
    if viewport:
        root.attributes["width"], root.attributes["height"] = width, height
    if view_box is not None:
        root.attributes["viewBox"] = view_box
    parts = layers(root)
    for run, item in parts:
        if run or len(parts) == 1:
            for leaf in hidden(root, run) if len(parts) > 1 else ():
                leaf.attributes[DISPLAY] = "none"
            _paint_svg(canvas, wrap(to_string(root, xml_declaration=False, pretty=False)), width, height)
            for leaf in hidden(root, run) if len(parts) > 1 else ():
                leaf.attributes.pop(DISPLAY, None)
        if isinstance(item, Text):
            draw_text(canvas, item, root, view)
        elif item is not None:
            draw_image(canvas, item, root, view)


def renderable_copy(root: Element, *, keep_text: Callable[[Text], bool] | None = None) -> Element:
    """A copy of *root* with every ``<text>`` replaced by its glyph outlines.

    Skia's SVG renderer draws no text, so text is drawn as paths. Styles are resolved,
    local image links embedded and ellipses converted to paths on the copy.

    Parameters
    ----------
    root : Element
        The tree to copy; it is not modified.
    keep_text : callable, optional
        Texts it accepts stay ``<text>`` elements (to be drawn as real glyphs). Defaults to None,
        which outlines every text.

    Returns
    -------
    Element
        A render-ready copy.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.render import renderable_copy
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 5, 5)
    >>> renderable_copy(doc.root) is doc.root
    False
    """
    from ..attributes.cascade import resolve_styles
    from ..elements.text import Text

    copy = root.clone()
    resolve_styles(copy)
    resolve_links(copy)
    _ellipses_as_paths(copy)
    _expand_image_patterns(copy)
    if isinstance(copy, Text):
        return copy if keep_text is not None and keep_text(copy) else _outlined(copy)
    for text in [e for e in copy.iter() if isinstance(e, Text)]:
        if keep_text is not None and keep_text(text):
            continue
        parent = text.parent
        assert parent is not None
        outline = _outlined(text)
        index = parent.children.index(text)
        parent.remove(text)
        parent.insert(index, outline)
    return copy


def _expand_image_patterns(root: Element) -> None:
    """Shapes filled with a pattern that holds images become clipped tiles, so the images get drawn."""
    from ..elements._geometry import PathOperand, replace_in_parent
    from ..elements.paint import Pattern

    for leaf in list(root.iter()):
        pattern = getattr(leaf.attributes.get("fill"), "element", None)
        if (isinstance(pattern, Pattern) and isinstance(leaf, PathOperand) and leaf.parent is not None
                and any(e.tag == "image" for e in pattern.iter())):
            try:
                replace_in_parent(leaf, leaf.expand_pattern())
            except (TypeError, ValueError):
                continue


def _ellipses_as_paths(root: Element) -> None:
    """Replace ``<ellipse>`` by an equal ``<path>`` (skia's SVG renderer paints gradients on ellipses black)."""
    from ..elements.shapes import Ellipse, Path

    for ellipse in [e for e in root.iter() if isinstance(e, Ellipse)]:
        parent = ellipse.parent
        if parent is None:
            continue
        path = Path(ellipse.local_outline())
        path.attributes.update((k, v) for k, v in ellipse.attributes.items() if k not in ellipse.geometry_attributes)
        index = parent.children.index(ellipse)
        parent.remove(ellipse)
        parent.insert(index, path)


def _outlined(text: Text) -> Element:
    """*text* as a ``<g>`` of per-run outline paths (keeps its transform, clip and opacity)."""
    from ..elements.structure import Group

    group = Group(*text.runs(), id=text.id, t=text.t)
    for name in ("clip-path", "mask", "filter", "opacity", "display", "visibility"):
        if text.has(name):
            group.attributes[name] = text.attributes[name]
    return group


def _view(document: Document, width: float, height: float, box: ViewBox | None = None) -> Matrix:
    box = box or document.root.view_box
    if box is None or not box.width or not box.height:
        return IDENTITY
    s = min(width / box.width, height / box.height)
    return (Matrix.translate((width - box.width * s) / 2, (height - box.height * s) / 2)
            @ Matrix.scale(s) @ Matrix.translate(-box.min_x, -box.min_y))


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
    return render_tree(document.root, lambda text: text, width, height, view=_view(document, width, height, box),
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
    from ..elements.animation import AnimationElement
    from ..video._smil import snapshot

    if document.root.find(AnimationElement) is not None:
        document = snapshot(document, time)
    image = document.rasterize(background="white", snapshot=True)
    info = skia.ImageInfo.Make(image.width(), image.height(), skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    frame = np.empty((image.height(), image.width(), 4), np.uint8)
    if not image.readPixels(info, frame, info.minRowBytes()):
        raise ValueError("skia could not read the frame")
    return frame
