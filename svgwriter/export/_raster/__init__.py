"""
Raster formats: PNG, JPEG, WebP, BMP, GIF and PPM out; ICO and ICNS icon families out and in; raster images and PNM in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from .._registry import register, register_importer

if TYPE_CHECKING:
    from ...color.color import ColorLike
    from ...document import Document

DEFAULT_QUALITY: Final = 90


def _raster(format: str):  # type: ignore[no-untyped-def]
    def exporter(document: Document, *, scale: float = 1.0, size: tuple[int, int] | int | None = None,
                 padding: float = 0.0, background: ColorLike | None = None, quality: int = DEFAULT_QUALITY) -> bytes:
        from ...ops.render import encode_image
        from ._encoders import ENCODERS, to_uint8

        if format == "jpeg" and background is None:
            background = "white"
        if isinstance(size, int):
            size = (size, size)
        native = format not in ENCODERS
        image = document.rasterize(scale=scale, size=size, padding=padding, background=background, snapshot=native)
        if not native:
            return ENCODERS[format](to_uint8(image))
        return encode_image(image, format, quality=quality)

    exporter.__doc__ = f"{format.upper()} raster (``scale``, ``size``, ``padding``, ``background``, ``quality``)."
    return exporter


register("png", extensions=(".png",))(_raster("png"))
register("jpeg", extensions=(".jpg", ".jpeg"))(_raster("jpeg"))
register("webp", extensions=(".webp",))(_raster("webp"))
register("bmp", extensions=(".bmp",))(_raster("bmp"))
register("gif", extensions=(".gif",))(_raster("gif"))
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
