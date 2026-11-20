"""
Raster formats: PNG, JPEG, WebP, BMP, GIF and PPM out; ICO and ICNS icon families out and in; raster images and PNM in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._internal._constants import DEFAULT_DPI
from .._registry import register, register_importer
from ._constants import DEFAULT_GIF_FPS, DEFAULT_QUALITY

if TYPE_CHECKING:
    from ...color.color import ColorLike
    from ...document import Document


def _frames(document: Document, fps: float, duration: float | None, **options: Any) -> list[Any]:
    """Every frame of the SMIL animation as uint8 RGBA, or an empty list when nothing animates."""
    from ...ops.parallel import rasterize_many
    from ...video.animation import animation_duration, frame_times
    from ._encoders import to_uint8

    processes = options.pop("processes", 1)
    length = duration if duration is not None else animation_duration(document)
    if not length:
        return []
    if isinstance(options.get("size"), int):
        options["size"] = (options["size"], options["size"])
    if processes == 1:
        return [to_uint8(document.at(time).rasterize(**options)) for time in frame_times(fps, length)]
    snapshots = [document.at(time) for time in frame_times(fps, length)]
    return rasterize_many(snapshots, processes=processes, dtype="uint8", **options)


def _animation_encoders() -> dict[str, Any]:
    from ._animated import encode_apng, encode_webp_animation

    return {"png": encode_apng, "webp": encode_webp_animation}


def _raster(format: str):  # type: ignore[no-untyped-def]
    def exporter(document: Document, *, scale: float = 1.0, size: tuple[int, int] | int | None = None,
                 padding: float = 0.0, background: ColorLike | None = None, quality: int = DEFAULT_QUALITY,
                 dpi: float | None = None, animate: bool = False, fps: float = DEFAULT_GIF_FPS,
                 duration: float | None = None, loop: int = 0, processes: int | None = 1) -> bytes:
        from ...ops.render import encode_image
        from ._encoders import ENCODERS, to_uint8

        if format == "jpeg" and background is None:
            background = "white"
        if isinstance(size, int):
            size = (size, size)
        if dpi is not None:
            scale = dpi / DEFAULT_DPI
        animated = _animation_encoders()
        if animate and format in animated:
            frames = _frames(document, fps, duration, scale=scale, size=size, padding=padding, background=background,
                             processes=processes)
            if frames:
                return animated[format](frames, fps, loop=loop)
        native = format not in ENCODERS
        image = document.rasterize(scale=scale, size=size, padding=padding, background=background, snapshot=native)
        if not native:
            return ENCODERS[format](to_uint8(image))
        return encode_image(image, format, quality=quality)

    exporter.__doc__ = (f"{format.upper()} raster (``scale`` or ``dpi``, ``size``, ``padding``, ``background``, "
                        "``quality``)" + ("; ``animate=True`` with ``fps``, ``duration``, ``loop`` writes the SMIL "
                                          "animation" if format in ("png", "webp") else "") + ".")
    return exporter


register("png", extensions=(".png",))(_raster("png"))
register("jpeg", extensions=(".jpg", ".jpeg"))(_raster("jpeg"))
register("webp", extensions=(".webp",))(_raster("webp"))
register("bmp", extensions=(".bmp",))(_raster("bmp"))


@register("gif", extensions=(".gif",))
def gif(document: Document, *, scale: float = 1.0, size: tuple[int, int] | int | None = None, padding: float = 0.0,
        background: ColorLike | None = None, animate: bool | None = None, fps: float = DEFAULT_GIF_FPS,
        duration: float | None = None, loop: int = 0, quality: int = DEFAULT_QUALITY,
        dpi: float | None = None, processes: int | None = 1) -> bytes:
    """GIF: a still image, or an animated GIF of the document's SMIL animation.

    Parameters
    ----------
    document : Document
        The drawing.
    scale, size, padding, background : optional
        As for PNG.
    animate : bool, optional
        Write every frame of the SMIL animation. Defaults to None, which
        animates when the document contains animation elements.
    fps : float, optional
        Frames per second of an animated GIF. Defaults to 12.
    duration : float, optional
        Seconds to record. Defaults to None, the end of the last animation.
    loop : int, optional
        Repeats; 0 loops forever. Defaults to 0.
    quality : int, optional
        Accepted like the other raster formats; GIF is lossless. Defaults to 90.
    dpi : float, optional
        Pixels per inch instead of `scale` (96 is scale 1). Defaults to None.
    processes : int, optional
        Worker processes for the frames; None uses every CPU. Defaults to 1.

    Returns
    -------
    bytes
        The GIF file.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(20, 10)
    >>> ball = doc.circle(2, 5, 2)
    >>> _ = ball.append(svg.Animate(attribute_name="cx", from_=2, to=18, dur=1))
    >>> svg.export.export(doc, "gif").count(b"NETSCAPE2.0")
    1
    """
    from ...elements.animation import AnimationElement
    from ...video.animation import animation_duration
    from ._encoders import encode_gif, encode_gif_animation, to_uint8

    del quality
    if dpi is not None:
        scale = dpi / DEFAULT_DPI
    if isinstance(size, int):
        size = (size, size)
    options = {"scale": scale, "size": size, "padding": padding, "background": background}
    length = duration if duration is not None else animation_duration(document)
    moving = animate if animate is not None else document.root.find(AnimationElement) is not None
    if not moving or not length:
        return encode_gif(to_uint8(document.rasterize(**options)))
    frames = _frames(document, fps, length, processes=processes, **options)
    return encode_gif_animation(frames, fps, loop=loop)
register("ppm", extensions=(".ppm", ".pgm", ".pnm"))(_raster("ppm"))


@register("ico", extensions=(".ico",))
def ico(document: Document, **options: Any) -> bytes:
    """Windows icon: square PNGs at ``sizes`` (16..256, ``padding`` in drawing units).

    Parameters
    ----------
    document : Document
        The drawing to rasterize at each size.
    **options
        ``sizes`` and ``padding``, as for :func:`~svgwriter.export._raster._icons.to_ico`.

    Returns
    -------
    bytes
        The ICO file.

    See Also
    --------
    icns : The macOS icon format.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(8, 8), "ico", sizes=(16,))[:4] == bytes.fromhex("00000100")
    True
    """
    from ._icons import to_ico

    return to_ico(document, **options)


@register("icns", extensions=(".icns",))
def icns(document: Document, **options: Any) -> bytes:
    """macOS icon family: PNGs at ``sizes`` (16..1024) under standard and Retina types.

    Parameters
    ----------
    document : Document
        The drawing to rasterize at each size.
    **options
        ``sizes`` and ``padding``, as for :func:`~svgwriter.export._raster._icons.to_icns`.

    Returns
    -------
    bytes
        The ICNS file.

    See Also
    --------
    ico : The Windows icon format.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(8, 8), "icns", sizes=(16,))[:4]
    b'icns'
    """
    from ._icons import to_icns

    return to_icns(document, **options)


@register_importer("icon", extensions=(".ico", ".icns"))
def read_icon(data: bytes) -> Document:
    """The largest image in an ICO or ICNS file.

    Parameters
    ----------
    data : bytes
        The icon file contents.

    Returns
    -------
    Document
        A document holding the image.

    Raises
    ------
    ValueError
        If the file holds no PNG image.

    See Also
    --------
    ico : Write an ICO file.

    Examples
    --------
    >>> import svgwriter as svg
    >>> data = svg.export.export(svg.Document(8, 8), "ico", sizes=(16,))
    >>> svg.export.find_importer(".ico").function(data).root.view_box.width
    16
    """
    from ._icons import read_icon as read

    return read(data)


@register_importer("image",extensions=(".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"))
def read_image(data: bytes) -> Document:
    """A raster image as a document holding one embedded ``<image>`` at its pixel size.

    Parameters
    ----------
    data : bytes
        PNG, JPEG, WebP, GIF, BMP or PNM file contents.

    Returns
    -------
    Document
        A document whose only child is the ``<image>``.

    See Also
    --------
    svgwriter.export.export : Rasterize a document to a PNG.

    Examples
    --------
    >>> import svgwriter as svg
    >>> png = svg.export.export(svg.Document(4, 2), "png")
    >>> doc = svg.export.find_importer(".png").function(png)
    >>> doc.root.view_box.width, len(doc)
    (4, 1)
    """
    from ...elements.structure import Pixels

    return _image_document(Pixels.decode(data))


@register_importer("pnm", extensions=(".ppm", ".pgm", ".pbm", ".pnm"))
def read_pnm(data: bytes) -> Document:
    """A PBM, PGM or PPM file as a document holding one embedded ``<image>`` at its pixel size.

    Parameters
    ----------
    data : bytes
        P1 to P6 file contents, ASCII or binary.

    Returns
    -------
    Document
        A document whose only child is the ``<image>``.

    Raises
    ------
    ValueError
        If the data is not a valid PNM file.

    See Also
    --------
    read_image : Other raster formats.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.export.find_importer(".pgm").function(b"P2\\n2 1\\n255\\n0 255\\n")
    >>> doc.root.view_box.width, len(doc)
    (2, 1)
    """
    from ...elements.structure import Pixels
    from ._encoders import decode_pnm

    return _image_document(Pixels.from_array(decode_pnm(data)))


def _image_document(pixels: Any) -> Document:
    """A document sized to the pixels, holding them as one ``<image>``."""
    from ...document import Document
    from ...elements.structure import Image

    rows, columns = pixels.shape
    document = Document(columns, rows)
    document.add(Image(pixels.rgba(), 0, 0, columns, rows))
    return document
