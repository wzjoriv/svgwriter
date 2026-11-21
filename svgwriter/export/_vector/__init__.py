"""
Vector page formats: PDF (via skia), TikZ and EPS, out and in.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import skia

from ..._internal._constants import PX_PER_INCH, PX_PER_PT
from .._registry import register, register_importer
from ._constants import PDF_LINK_KEY

if TYPE_CHECKING:
    from ..._internal._color._icc_output import IccLike
    from ...document import Document


@register("pdf", extensions=(".pdf",), multipage=True)
def pdf(document: Document | Sequence[Document], *, title: str | None = None, author: str | None = None,
        text: bool = True, px_per_inch: float = PX_PER_INCH, icc: IccLike | None = None) -> bytes:
    """Vector PDF drawn by skia: shapes stay vector, text stays selectable, images are embedded.

    Pages have the document's physical size: a user unit (CSS pixel) is 3/4 of a point, 96 per
    inch, so a ``210mm`` by ``297mm`` document prints as an A4 page.

    Text painted with plain colours is written as real text in an embedded font subset, so it can
    be selected, searched and copied. Links (``<a href>``) become clickable areas. Text with a gradient or pattern paint, a filter or a mask,
    and characters that need a shaper (Devanagari, Arabic, ...), are drawn as exact glyph outlines.

    Parameters
    ----------
    document : Document or sequence of Document
        The document to draw, or several documents for one page each; every
        page has its own document's size.
    title : str, optional
        PDF title metadata. Defaults to None.
    author : str, optional
        PDF author metadata. Defaults to None.
    text : bool, optional
        Keep text as text where possible; False draws every glyph as an outline. Defaults to True.
    px_per_inch : float, optional
        User units per inch of a document sized in pixels or plain numbers: 72 prints one unit as
        one point. Sizes in ``mm``, ``cm``, ``in``, ``pt`` or ``pc`` are kept. Defaults to 96 (CSS).
    icc : {"srgb"} or bytes, optional
        An output intent with this ICC profile: ``"srgb"`` declares the page colours sRGB
        (as PDF/A expects), CMYK profile bytes name the printing condition (as PDF/X expects).
        The colours stay sRGB, since skia writes only DeviceRGB, so other RGB profiles are refused.
        Needs the ``color`` extra. Defaults to None.

    Returns
    -------
    bytes
        The PDF file.

    Raises
    ------
    ValueError
        If `px_per_inch` is not above 0 or `icc` is not sRGB or a CMYK profile.
    ImportError
        If `icc` is given without the ``color`` extra.

    See Also
    --------
    eps : Encapsulated PostScript output.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(4, 4), "pdf", title="demo")[:5]
    b'%PDF-'
    """
    from ..._internal._rendering import view_matrix
    from ...ops.render import page_size, paint_tree
    from ._pdf_boxes import exact_media_boxes, page_points
    from ._units import unit_scale

    stream = skia.DynamicMemoryWStream()
    metadata = skia.PDF.Metadata()
    if title:
        metadata.fTitle = title
    if author:
        metadata.fAuthor = author
    pdf_document = skia.PDF.MakeDocument(stream, metadata)
    sizes: list[tuple[float, float]] = []
    for page in document if isinstance(document, Sequence) else [document]:
        with page._prepared():
            width, height = page_size(page)
            points = PX_PER_PT / unit_scale(page, px_per_inch)
            sizes.append((width / points, height / points))
            canvas = pdf_document.beginPage(*page_points(*sizes[-1]))
            canvas.scale(1 / points, 1 / points)
            paint_tree(canvas, page.root, lambda text: text, width, height,
                       view=view_matrix(page, width, height), viewport=True, native_text=text)
        _links(canvas, page)
        pdf_document.endPage()
    pdf_document.close()
    data = exact_media_boxes(bytes(stream.detachAsData()), sizes)
    if icc is None:
        return data
    from ..._internal._color._icc_output import output_profile
    from ._pdf_intent import with_output_intent

    return with_output_intent(data, output_profile(icc))


def _links(canvas: skia.Canvas, page: Document) -> None:
    """A clickable URL area over every ``<a href>`` of *page*."""
    from ..._internal._rendering import page_box

    for anchor in [element for element in page.root.iter() if element.tag == "a"]:
        target = str(anchor.get("href") or anchor.get("xlink:href") or "")
        box, _ = page_box(page, anchor)
        if target and box is not None:
            canvas.drawAnnotation(skia.Rect.MakeXYWH(*box), PDF_LINK_KEY, skia.Data(target.encode() + b"\0"))


@register("tikz", extensions=(".tikz", ".tex"), binary=False)
def tikz(document: Document, *, standalone: bool = False, text: bool = True, px_per_inch: float = PX_PER_INCH) -> str:
    """A TikZ picture of the flattened vector content (gradients as shadings; images skipped).

    Parameters
    ----------
    document : Document
        The document to convert.
    standalone : bool, optional
        Wrap the picture in a compilable ``standalone`` LaTeX document. Defaults to False.
    text : bool, optional
        Write text as ``\\node`` commands typeset by LaTeX; False draws the exact glyph outlines.
        Defaults to True.
    px_per_inch : float, optional
        User units per inch of a document sized in pixels; 72 draws one unit as one point. Sizes
        in ``mm``, ``cm``, ``in``, ``pt`` or ``pc`` are kept. Defaults to 96.

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

    return to_tikz(document, standalone=standalone, text=text, px_per_inch=px_per_inch)


@register("eps", extensions=(".eps", ".ps"))
def eps(document: Document, *, text: bool = True, px_per_inch: float = PX_PER_INCH) -> bytes:
    """Encapsulated PostScript of the flattened vector content (solid paints; images skipped).

    Parameters
    ----------
    document : Document
        The document to convert.
    text : bool, optional
        Write text with PostScript fonts; False draws the exact glyph outlines. Defaults to True.
    px_per_inch : float, optional
        User units per inch of a document sized in pixels; 72 draws one unit as one point. Sizes
        in ``mm``, ``cm``, ``in``, ``pt`` or ``pc`` are kept. Defaults to 96.

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

    return to_eps(document, text=text, px_per_inch=px_per_inch).encode("ascii")


@register_importer("pdf", extensions=(".pdf",), page_option="page")
def read_pdf(data: bytes, *, page: int | None = 0) -> Document | list[Document]:
    """The paths, images, clips and text of a PDF page as elements.

    Parameters
    ----------
    data : bytes
        The PDF file.
    page : int or None, optional
        Zero-based index of the page to read, or None for every page. Defaults to 0.

    Returns
    -------
    Document or list of Document
        A document the size of the page in user units (96 per inch, so 4/3 per point), y pointing down; a list
        with one per page when *page* is None.

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
    the path, line-style and colour operators and ``gs`` alpha, images,
    clipping, text, shadings and tiling patterns; see
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
    from ._pdf_read import page_count
    from ._pdf_read import read_pdf as read

    if page is None:
        return [read(data, page=index) for index in range(page_count(data))]
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
        The drawing in user units (96 per inch), y pointing down.

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
        The drawing in user units (4/3 per point), y pointing down, sized to its bounding box.

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
