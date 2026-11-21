"""
Raster formats: PNG, JPEG, WebP, BMP, GIF, PPM and TIFF out; ICO and ICNS icon families out and in; raster images and PNM in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._internal._constants import PX_PER_INCH
from .._registry import register, register_importer
from .._units import dpi_scale
from . import _tiff  # noqa: F401
from ._constants import DEFAULT_GIF_FPS, DEFAULT_QUALITY, ICC_FORMATS

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..._internal._color._icc_output import IccLike
    from ...document import Document
    from ...model.color.color import ColorLike


def _frames(document: Document, fps: float, duration: float | None, **options: Any) -> list[Any]:
    """Every frame of the SMIL animation as uint8 RGBA, or an empty list when nothing animates."""
    from ..._internal._codecs._rgba import to_uint8
    from ...ops.parallel import rasterize_many
    from ...video.animation import animation_duration, frame_times

    processes = options.pop("processes", 1)
    length = duration if duration is not None else animation_duration(document)
    if not length:
        return []
    if isinstance(options.get("pixels"), int):
        options["pixels"] = (options["pixels"], options["pixels"])
    if processes == 1:
        return [to_uint8(document.at(seconds).rasterize(**options)) for seconds in frame_times(fps, length)]
    snapshots = [document.at(seconds) for seconds in frame_times(fps, length)]
    return rasterize_many(snapshots, processes=processes, dtype="uint8", **options)


def _animation_encoders() -> dict[str, Any]:
    from ._animated import encode_apng, encode_webp_animation

    return {"png": encode_apng, "webp": encode_webp_animation}


def _profiled(frames: list[Any], icc: IccLike | None, encoder: Callable[[list[Any]], bytes]) -> bytes:
    """Encode sRGB *frames*, first converted to the *icc* profile, with the profile embedded."""
    if icc is None:
        return encoder(frames)
    from ..._internal._color._icc_embedded import embed_profile
    from ..._internal._color._icc_output import output_profile, to_profile

    target = output_profile(icc)
    if target.space != "RGB":
        raise ValueError(f"PNG and JPEG take RGB profiles, not {target.space}; export CMYK as tiff or pdf")
    return embed_profile(encoder(frames if target.srgb else [to_profile(frame, target) for frame in frames]), target.data)


def _is_srgb(icc: IccLike) -> bool:
    """Whether *icc* names sRGB, so the rendered pixels are written as they are."""
    from ..._internal._color._icc_output import output_profile

    return output_profile(icc).srgb


def _raster(format: str) -> Callable[..., bytes]:
    def exporter(document: Document, *, scale: float | None = None, pixels: tuple[int, int] | int | None = None,
                 padding: float = 0.0, background: ColorLike | None = None, quality: int = DEFAULT_QUALITY,
                 dpi: float | None = None, units_per_inch: float = PX_PER_INCH, animate: bool = False, fps: float = DEFAULT_GIF_FPS,
                 duration: float | None = None, loop: int = 0, processes: int | None = 1,
                 icc: IccLike | None = None) -> bytes:
        from ..._internal._codecs._encoders import ENCODERS
        from ..._internal._codecs._rgba import to_uint8
        from ...inkscape import export_hints
        from ...ops.render import encode_image

        if icc is not None and format not in ICC_FORMATS:
            raise ValueError(f"{format} cannot embed an ICC profile; use one of {', '.join(ICC_FORMATS)} or tiff")
        if format == "jpeg" and background is None:
            background = "white"
        if isinstance(pixels, int):
            pixels = (pixels, pixels)
        if dpi is None and scale is None and pixels is None:
            dpi = export_hints(document.root).dpi
        scale = dpi_scale(document, dpi, units_per_inch) if dpi is not None else 1.0 if scale is None else scale
        animated = _animation_encoders()
        if animate and format in animated:
            frames = _frames(document, fps, duration, scale=scale, pixels=pixels, padding=padding, background=background,
                             processes=processes)
            if frames:
                return _profiled(frames, icc, lambda done: animated[format](done, fps, loop=loop))
        if icc is not None and not _is_srgb(icc):
            from ...ops.render import encode

            still = [to_uint8(document.rasterize(scale=scale, pixels=pixels, padding=padding, background=background))]
            return _profiled(still, icc, lambda done: encode(done[0], format, quality=quality))
        if icc is not None:
            image = document.rasterize(scale=scale, pixels=pixels, padding=padding, background=background, snapshot=True)
            return _profiled([image], icc, lambda done: encode_image(done[0], format, quality=quality))
        native = format not in ENCODERS
        image = document.rasterize(scale=scale, pixels=pixels, padding=padding, background=background, snapshot=native)
        if not native:
            return ENCODERS[format](to_uint8(image))
        return encode_image(image, format, quality=quality)

    exporter.__doc__ = (f"{format.upper()} raster (``scale`` or ``dpi`` with ``units_per_inch``, defaulting to Inkscape's "
                        "``inkscape:export-xdpi`` when the document has one, ``pixels``, ``padding``, ``background``, "
                        "``quality``" + (", ``icc`` (``'srgb'``, ``'display-p3'`` or RGB profile bytes: the sRGB pixels are "
                                         "converted and the profile embedded)" if format in ICC_FORMATS else "")
                        + ")" + ("; ``animate=True`` with ``fps``, ``duration``, ``loop`` writes the SMIL "
                                          "animation" if format in ("png", "webp") else "") + ".")
    return exporter


register("png", extensions=(".png",))(_raster("png"))
register("jpeg", extensions=(".jpg", ".jpeg"))(_raster("jpeg"))
register("webp", extensions=(".webp",))(_raster("webp"))
register("bmp", extensions=(".bmp",))(_raster("bmp"))


@register("gif", extensions=(".gif",))
def gif(document: Document, *, scale: float = 1.0, pixels: tuple[int, int] | int | None = None, padding: float = 0.0,
        background: ColorLike | None = None, animate: bool | None = None, fps: float = DEFAULT_GIF_FPS,
        duration: float | None = None, loop: int = 0, quality: int = DEFAULT_QUALITY,
        dpi: float | None = None, units_per_inch: float = PX_PER_INCH, processes: int | None = 1) -> bytes:
    """GIF: a still image, or an animated GIF of the document's SMIL animation.

    Parameters
    ----------
    document : Document
        The drawing.
    scale, pixels, padding, background : optional
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
    dpi, units_per_inch : float, optional
        As for PNG: pixels per printed inch instead of `scale`, and user units per inch of a page
        sized in plain numbers. Default to None and 96.
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
    from ..._internal._codecs._gif import encode_gif, encode_gif_animation
    from ..._internal._codecs._rgba import to_uint8
    from ...model.elements.animation import AnimationElement
    from ...video.animation import animation_duration

    del quality
    if dpi is not None:
        scale = dpi_scale(document, dpi, units_per_inch)
    if isinstance(pixels, int):
        pixels = (pixels, pixels)
    options = {"scale": scale, "pixels": pixels, "padding": padding, "background": background}
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
    from ...model.elements.structure import Pixels

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
    from ..._internal._codecs._pnm import decode_pnm
    from ...model.elements.structure import Pixels

    return _image_document(Pixels.from_array(decode_pnm(data)))


def _image_document(pixels: Any) -> Document:
    """A document sized to the pixels, holding them as one ``<image>``."""
    from ...document import Document
    from ...model.elements.structure import Image

    rows, columns = pixels.shape
    document = Document(columns, rows)
    document.add(Image(pixels.rgba(), 0, 0, columns, rows))
    return document
