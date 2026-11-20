"""
Vector page formats: PDF (via skia), TikZ and EPS, out and in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import skia

from .._registry import register, register_importer

if TYPE_CHECKING:
    from ...document import Document


@register("pdf", extensions=(".pdf",))
def pdf(document: Document, *, title: str | None = None, author: str | None = None, text: bool = True) -> bytes:
    """Single-page vector PDF drawn by skia: shapes stay vector, text stays selectable, images are embedded.

    Text painted with plain colours is written as real text in an embedded font subset, so it can
    be selected, searched and copied. Text with a gradient or pattern paint, a filter or a mask,
    and characters that need a shaper (Devanagari, Arabic, ...), are drawn as exact glyph outlines.

    Parameters
    ----------
    document : Document
        The document to draw; the page has the document's size.
    title : str, optional
        PDF title metadata. Defaults to None.
    author : str, optional
        PDF author metadata. Defaults to None.
    text : bool, optional
        Keep text as text where possible; False draws every glyph as an outline. Defaults to True.

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
                   view=_view(document, width, height), viewport=True, native_text=text)
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
def eps(document: Document, *, text: bool = True) -> bytes:
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

    return to_eps(document, text=text).encode("ascii")


@register_importer("pdf", extensions=(".pdf",))
def read_pdf(data: bytes, *, page: int = 0) -> Document:
    """The vector paths of one PDF page as filled and stroked paths (text and images skipped).

    Parameters
    ----------
    data : bytes
        The PDF file.
    page : int, optional
        Zero-based index of the page to read. Defaults to 0.

    Returns
    -------
    Document
        A document the size of the page in points, y pointing down.

    Raises
    ------
    ValueError
        If *data* is not a readable PDF or has no page *page*.

    See Also
    --------
    pdf : Write PDF.

    Notes
    -----
    Supported: objects found by scanning (no xref table needed), object
    streams, uncompressed and ``/FlateDecode`` content streams, Form XObjects,
    the path, line-style and colour operators and ``gs`` alpha. Text, images,
    shadings, patterns and clipping are not read; see
    :func:`~svgwriter.export._vector._pdf_read.read_pdf` for the full subset.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> data = svg.export.export(doc, "pdf")
    >>> svg.export.find_importer(".pdf").function(data)[0].get("fill")
    '#ff0000'
    """
    from ._pdf_read import read_pdf as read

    return read(data, page=page)


@register_importer("tikz", extensions=(".tikz", ".tex"))
def read_tikz(data: bytes) -> Document:
    """TikZ ``\\draw``, ``\\fill``, ``\\filldraw`` and ``\\path`` commands as paths.

    Parameters
    ----------
    data : bytes
        The LaTeX source, UTF-8 encoded.

    Returns
    -------
    Document
        The drawing in points, y pointing down.

    Raises
    ------
    ValueError
        If the source has no TikZ picture or path command.

    See Also
    --------
    tikz : Write TikZ.

    Notes
    -----
    Reads what :func:`tikz` writes and common hand-written pictures: straight
    and Bézier segments, ``cycle``, ``rectangle``, ``circle``, colours with
    ``\\definecolor``, ``draw=``, ``fill=``, ``line width=``, opacity and
    dashes, plus nodes, styles, scopes and ``\\foreach`` loops. Macros are not read; see
    :func:`~svgwriter.export._vector._tikz_read.read_tikz` for the full subset.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> data = svg.export.export(doc, "tikz").encode()
    >>> svg.export.find_importer(".tex").function(data)[0].get("fill")
    '#ff0000'
    """
    from ._tikz_read import read_tikz as read

    return read(data.decode("utf-8", "replace"))


@register_importer("eps", extensions=(".eps", ".ps"))
def read_eps(data: bytes) -> Document:
    """EPS and PostScript drawings as paths, run by a small PostScript interpreter.

    Parameters
    ----------
    data : bytes
        The PostScript program.

    Returns
    -------
    Document
        The drawing in points, y pointing down, sized to its bounding box.

    Raises
    ------
    ValueError
        If *data* is not PostScript.

    See Also
    --------
    eps : Write EPS.

    Notes
    -----
    Reads what :func:`eps` writes and simple EPS files: path construction,
    ``arc``, painting, colours, line styles, ``gsave``/``grestore``,
    transforms and procedures defined with ``def``. Unknown operators are
    ignored; text, images, clipping and control flow are not read. See
    :func:`~svgwriter.export._vector._eps_read.read_eps` for the full subset.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> data = svg.export.export(doc, "eps")
    >>> svg.export.find_importer(".eps").function(data)[0].get("fill")
    '#ff0000'
    """
    from ._eps_read import read_eps as read

    return read(data)
