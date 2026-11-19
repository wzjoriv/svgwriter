"""
Built-in formats: SVG, SVGZ, PNG, JPEG, WebP, PDF, TikZ and EPS out; SVG, SVGZ and raster images in.
"""

from __future__ import annotations

import gzip
from typing import TYPE_CHECKING, Any, Final

import skia

from ._registry import register, register_importer

if TYPE_CHECKING:
    from ..document import Document

DEFAULT_QUALITY: Final = 90
GZIP_MAGIC: Final = b"\x1f\x8b"


@register("svg", extensions=(".svg",), binary=False)
def svg_text(document: Document, **options: Any) -> str:
    """SVG 1.1 text (links, ``<a>`` and ids preserved); options as :class:`~svgwriter.io.SerializeOptions`.

    Parameters
    ----------
    document : Document
        The document to serialize.
    **options
        Serialization options.

    Returns
    -------
    str
        The SVG source.

    See Also
    --------
    svgz : The gzip-compressed form.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(4, 4), "svg").startswith("<?xml")
    True
    """
    return document.to_string(**options)


@register("svgz", extensions=(".svgz",))
def svgz(document: Document, **options: Any) -> bytes:
    """Gzip-compressed SVG.

    Parameters
    ----------
    document : Document
        The document to serialize.
    **options
        Serialization options, as for the ``svg`` format.

    Returns
    -------
    bytes
        A gzip stream (with a zero timestamp, so output is reproducible).

    See Also
    --------
    svg_text : The uncompressed form.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(4, 4), "svgz")[:2] == bytes.fromhex("1f8b")
    True
    """
    return gzip.compress(document.to_string(**options).encode("utf-8"), mtime=0)


def _raster(format: str):  # type: ignore[no-untyped-def]
    def exporter(document: Document, *, scale: float = 1.0, size: tuple[int, int] | int | None = None,
                 padding: float = 0.0, background: str | None = None, quality: int = DEFAULT_QUALITY) -> bytes:
        from ..ops.render import encode_image

        if format == "jpeg" and background is None:
            background = "white"
        if isinstance(size, int):
            size = (size, size)
        image = document.rasterize(scale=scale, size=size, padding=padding, background=background, snapshot=True)
        return encode_image(image, format, quality=quality)

    exporter.__doc__ = f"{format.upper()} raster (``scale``, ``size``, ``padding``, ``background``, ``quality``)."
    return exporter


register("png", extensions=(".png",))(_raster("png"))
register("jpeg", extensions=(".jpg", ".jpeg"))(_raster("jpeg"))
register("webp", extensions=(".webp",))(_raster("webp"))


@register("pdf", extensions=(".pdf",))
def pdf(document: Document, *, title: str | None = None, author: str | None = None) -> bytes:
    """Single-page vector PDF drawn by skia (shapes and text stay vector; images embedded).

    Parameters
    ----------
    document : Document
        The document to draw; the page has the document's size.
    title : str, optional
        PDF title metadata. Defaults to None.
    author : str, optional
        PDF author metadata. Defaults to None.

    Returns
    -------
    bytes
        The PDF file.

    See Also
    --------
    eps : Encapsulated PostScript output.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(4, 4), "pdf", title="demo")[:5]
    b'%PDF-'
    """
    from ..ops.render import _view, document_size, paint_tree

    width, height = document_size(document)
    stream = skia.DynamicMemoryWStream()
    metadata = skia.PDF.Metadata()
    if title:
        metadata.fTitle = title
    if author:
        metadata.fAuthor = author
    pdf_document = skia.PDF.MakeDocument(stream, metadata)
    with document._sized():
        width, height = document_size(document)
        canvas = pdf_document.beginPage(width, height)
        paint_tree(canvas, document.root, lambda text: text, width, height,
                   view=_view(document, width, height), viewport=True)
        pdf_document.endPage()
    pdf_document.close()
    return bytes(stream.detachAsData())


@register("tikz", extensions=(".tikz", ".tex"), binary=False)
def tikz(document: Document, *, standalone: bool = False) -> str:
    """A TikZ picture of the flattened vector content (solid paints; images skipped).

    Parameters
    ----------
    document : Document
        The document to convert.
    standalone : bool, optional
        Wrap the picture in a compilable ``standalone`` LaTeX document. Defaults to False.

    Returns
    -------
    str
        LaTeX source.

    See Also
    --------
    eps : Encapsulated PostScript output.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> "tikzpicture" in svg.export.export(doc, "tikz")
    True
    """
    from ._tikz import to_tikz

    return to_tikz(document, standalone=standalone)


@register("eps", extensions=(".eps", ".ps"))
def eps(document: Document) -> bytes:
    """Encapsulated PostScript of the flattened vector content (solid paints; images skipped).

    Parameters
    ----------
    document : Document
        The document to convert.

    Returns
    -------
    bytes
        ASCII PostScript source.

    See Also
    --------
    tikz : TikZ output.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(4, 4), "eps")[:4]
    b'%!PS'
    """
    from ._eps import to_eps

    return to_eps(document).encode("ascii")


@register("dxf", extensions=(".dxf",), binary=False)
def dxf(document: Document, **options: Any) -> str:
    """AutoCAD DXF R12 polylines in mm (``tolerance``, ``unit_mm``).

    Parameters
    ----------
    document : Document
        The document to convert.
    **options
        ``tolerance`` and ``unit_mm``, as for :func:`~svgwriter.export._cnc.to_dxf`.

    Returns
    -------
    str
        DXF text.

    See Also
    --------
    read_dxf : Read DXF back.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> "POLYLINE" in svg.export.export(doc, "dxf")
    True
    """
    from ._cnc import to_dxf

    return to_dxf(document, **options)


@register("hpgl", extensions=(".hpgl", ".plt"), binary=False)
def hpgl(document: Document, **options: Any) -> str:
    """HPGL for pen plotters and vinyl cutters, one pen per colour (``tolerance``, ``unit_mm``).

    Parameters
    ----------
    document : Document
        The document to convert.
    **options
        ``tolerance`` and ``unit_mm``, as for :func:`~svgwriter.export._cnc.to_hpgl`.

    Returns
    -------
    str
        HPGL text.

    See Also
    --------
    read_hpgl : Read HPGL back.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> svg.export.export(doc, "hpgl").startswith("IN;")
    True
    """
    from ._cnc import to_hpgl

    return to_hpgl(document, **options)


@register("gcode", extensions=(".gcode", ".nc", ".ngc"), binary=False)
def gcode(document: Document, **options: Any) -> str:
    """G-code toolpaths for CNC mills and lasers (``feed``, ``mode``, ``cut_z``, ``tolerance``, ...).

    Parameters
    ----------
    document : Document
        The document to convert.
    **options
        Keyword options of :func:`~svgwriter.export._cnc.to_gcode`.

    Returns
    -------
    str
        G-code text.

    See Also
    --------
    read_gcode : Read G-code back.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> svg.export.export(doc, "gcode", mode="laser").startswith("G21")
    True
    """
    from ._cnc import to_gcode

    return to_gcode(document, **options)


@register("ico", extensions=(".ico",))
def ico(document: Document, **options: Any) -> bytes:
    """Windows icon: square PNGs at ``sizes`` (16..256, ``padding`` in drawing units).

    Parameters
    ----------
    document : Document
        The drawing to rasterize at each size.
    **options
        ``sizes`` and ``padding``, as for :func:`~svgwriter.export._icons.to_ico`.

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
        ``sizes`` and ``padding``, as for :func:`~svgwriter.export._icons.to_icns`.

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


@register_importer("svg", extensions=(".svg", ".svgz"))
def read_svg(data: bytes, **options: Any) -> Document:
    """SVG or gzip-compressed SVG.

    Parameters
    ----------
    data : bytes
        The file contents; gzip data is detected and decompressed.
    **options
        Passed to :meth:`~svgwriter.Document.from_string`.

    Returns
    -------
    Document
        The parsed document.

    See Also
    --------
    svg_text : Write SVG.

    Examples
    --------
    >>> import svgwriter as svg
    >>> data = svg.export.export(svg.Document(4, 4), "svgz")
    >>> svg.export.find_importer(".svgz").function(data).root.tag
    'svg'
    """
    from ..document import Document

    if data[:2] == GZIP_MAGIC:
        data = gzip.decompress(data)
    return Document.from_string(data, **options)


@register_importer("dxf", extensions=(".dxf",))
def read_dxf(data: bytes, **options: Any) -> Document:
    """DXF lines, polylines, circles, arcs and ellipses as stroked paths.

    Parameters
    ----------
    data : bytes
        The DXF text, UTF-8 encoded.
    **options
        ``unit_mm``, as for :func:`~svgwriter.export._cnc_read.read_dxf`.

    Returns
    -------
    Document
        A document with one stroked path per entity.

    See Also
    --------
    dxf : Write DXF.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> data = svg.export.export(doc, "dxf").encode()
    >>> len(svg.export.find_importer(".dxf").function(data)) > 0
    True
    """
    from ._cnc_read import read_dxf as read

    return read(data.decode("utf-8", "replace"), **options)


@register_importer("hpgl", extensions=(".hpgl", ".plt"))
def read_hpgl(data: bytes, **options: Any) -> Document:
    """HPGL pen moves as stroked paths, coloured by pen.

    Parameters
    ----------
    data : bytes
        The HPGL text, ASCII encoded.
    **options
        ``unit_mm``, as for :func:`~svgwriter.export._cnc_read.read_hpgl`.

    Returns
    -------
    Document
        A document with one stroked path per pen-down run.

    See Also
    --------
    hpgl : Write HPGL.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> data = svg.export.export(doc, "hpgl").encode()
    >>> len(svg.export.find_importer(".hpgl").function(data)) > 0
    True
    """
    from ._cnc_read import read_hpgl as read

    return read(data.decode("ascii", "replace"), **options)


@register_importer("gcode", extensions=(".gcode", ".nc", ".ngc"))
def read_gcode(data: bytes, **options: Any) -> Document:
    """G-code cutting moves as stroked paths.

    Parameters
    ----------
    data : bytes
        The G-code text, ASCII encoded.
    **options
        ``unit_mm``, as for :func:`~svgwriter.export._cnc_read.read_gcode`.

    Returns
    -------
    Document
        A document with one stroked path per cutting run.

    See Also
    --------
    gcode : Write G-code.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> data = svg.export.export(doc, "gcode").encode()
    >>> len(svg.export.find_importer(".gcode").function(data)) > 0
    True
    """
    from ._cnc_read import read_gcode as read

    return read(data.decode("ascii", "replace"), **options)


@register("excalidraw", extensions=(".excalidraw",), binary=False)
def excalidraw(document: Document, **options: Any) -> str:
    """Excalidraw scene JSON (outlines as line elements).

    Parameters
    ----------
    document : Document
        The document to convert.
    **options
        Keyword options of :func:`~svgwriter.export._excalidraw.to_excalidraw`.

    Returns
    -------
    str
        The scene as JSON text.

    See Also
    --------
    read_excalidraw : Read a scene back.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(4, 4), "excalidraw").count("excalidraw") > 0
    True
    """
    from ._excalidraw import to_excalidraw

    return to_excalidraw(document, **options)


@register_importer("excalidraw", extensions=(".excalidraw", ".json"))
def read_excalidraw(data: bytes) -> Document:
    """Excalidraw scene JSON as native SVG shapes, text and images.

    Parameters
    ----------
    data : bytes
        The scene JSON, UTF-8 encoded.

    Returns
    -------
    Document
        The drawing as a document.

    See Also
    --------
    excalidraw : Write a scene.

    Examples
    --------
    >>> import svgwriter as svg
    >>> data = svg.export.export(svg.Document(4, 4), "excalidraw").encode()
    >>> svg.export.find_importer(".excalidraw").function(data).root.tag
    'svg'
    """
    from ._excalidraw import read_excalidraw as read

    return read(data.decode("utf-8"))


@register_importer("image",extensions=(".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"))
def read_image(data: bytes) -> Document:
    """A raster image as a document holding one embedded ``<image>`` at its pixel size.

    Parameters
    ----------
    data : bytes
        PNG, JPEG, WebP, GIF or BMP file contents.

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
    from ..document import Document
    from ..elements.structure import Image, Pixels

    pixels = Pixels.decode(data)
    rows, columns = pixels.shape
    document = Document(columns, rows)
    image = Image(pixels.rgba(), 0, 0, columns, rows)
    document.add(image)
    return document
