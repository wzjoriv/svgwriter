"""
Vector page formats: PDF (via skia), TikZ and EPS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import skia

from .._registry import register

if TYPE_CHECKING:
    from ...document import Document


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
    from ...ops.render import _view, document_size, paint_tree

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
