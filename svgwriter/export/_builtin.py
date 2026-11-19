"""Built-in formats: SVG, SVGZ, PNG, JPEG, WebP, PDF, TikZ and EPS out; SVG, SVGZ and raster images in."""

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
    """SVG 1.1 text (links, ``<a>`` and ids preserved); options as :class:`~svgwriter.io.SerializeOptions`."""
    return document.to_string(**options)


@register("svgz", extensions=(".svgz",))
def svgz(document: Document, **options: Any) -> bytes:
    """Gzip-compressed SVG."""
    return gzip.compress(document.to_string(**options).encode("utf-8"), mtime=0)


def _raster(format: str):  # type: ignore[no-untyped-def]
    def exporter(document: Document, *, scale: float = 1.0, size: tuple[int, int] | None = None,
                 background: str | None = None, quality: int = DEFAULT_QUALITY) -> bytes:
        from ..ops.render import encode

        if format == "jpeg" and background is None:
            background = "white"
        return encode(document.rasterize(scale=scale, size=size, background=background), format, quality=quality)

    exporter.__doc__ = f"{format.upper()} raster (``scale``, ``size``, ``background``, ``quality``)."
    return exporter


register("png", extensions=(".png",))(_raster("png"))
register("jpeg", extensions=(".jpg", ".jpeg"))(_raster("jpeg"))
register("webp", extensions=(".webp",))(_raster("webp"))


@register("pdf", extensions=(".pdf",))
def pdf(document: Document, *, title: str | None = None, author: str | None = None) -> bytes:
    """Single-page vector PDF drawn by skia (shapes and text stay vector; images embedded)."""
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
    """A TikZ picture of the flattened vector content (solid paints; images skipped)."""
    from ._tikz import to_tikz

    return to_tikz(document, standalone=standalone)


@register("eps", extensions=(".eps", ".ps"))
def eps(document: Document) -> bytes:
    """Encapsulated PostScript of the flattened vector content (solid paints; images skipped)."""
    from ._eps import to_eps

    return to_eps(document).encode("ascii")


@register_importer("svg", extensions=(".svg", ".svgz"))
def read_svg(data: bytes, **options: Any) -> Document:
    """SVG or gzip-compressed SVG."""
    from ..document import Document

    if data[:2] == GZIP_MAGIC:
        data = gzip.decompress(data)
    return Document.from_string(data, **options)


@register_importer("image", extensions=(".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"))
def read_image(data: bytes) -> Document:
    """A raster image as a document holding one embedded ``<image>`` at its pixel size."""
    from ..document import Document
    from ..elements.structure import Image, Pixels

    pixels = Pixels.decode(data)
    rows, columns = pixels.shape
    document = Document(columns, rows)
    image = Image(pixels.rgba(), 0, 0, columns, rows)
    document.add(image)
    return document
