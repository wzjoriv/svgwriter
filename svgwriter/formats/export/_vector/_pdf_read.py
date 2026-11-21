"""
Reading the vector paths of a PDF page back into a document.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...._internal._constants import PX_PER_PT
from ....model.transform.matrix import Matrix
from ._constants import ENCRYPT_RE, HEADER_WINDOW, PDF_HEADER
from ._pdf_objects import _content, _inherited, _media_box, _objects, _pages
from ._pdf_painter import _Painter
from ._reading import to_document

if TYPE_CHECKING:
    from ....document import Document

__all__ = ["page_count", "read_pdf"]


def read_pdf(data: bytes, *, page: int = 0) -> Document:
    """Read the vector paths of one PDF page as filled and stroked ``<path>`` elements.

    Parameters
    ----------
    data : bytes
        The PDF file.
    page : int, optional
        Zero-based index of the page to read. Defaults to 0.

    Returns
    -------
    Document
        A document the size of the page's ``MediaBox`` in user units, 96 per inch
        (4/3 per point), y pointing down.

    Raises
    ------
    ValueError
        If *data* is not a PDF, is encrypted, has no pages, or has no page *page*.

    See Also
    --------
    svgwriter.formats.export._vector._eps_read.read_eps : Read PostScript.

    Notes
    -----
    Objects are found by scanning for ``N G obj``, so a broken cross-reference
    table does not matter; object streams are unpacked. Supported: content
    streams that are uncompressed or ``/FlateDecode`` (other filters are
    skipped), Form XObjects drawn with ``Do`` (transparency groups take the
    current fill alpha), the path operators ``m l c v y h re`` and
    ``S s f F f* B B* b b* n``, the state operators ``q Q cm w J j M d`` and
    ``gs`` (``CA``, ``ca``, ``LW``, ``LC``, ``LJ``, ``ML``, ``D``), and the
    colour operators ``rg RG g G k K`` plus ``cs``/``sc``/``scn`` read by
    operand count as gray, RGB or CMYK. Images (JPEG, or Flate-compressed
    gray/RGB/CMYK samples with soft masks) become ``<image>`` elements,
    clipping paths (``W``, ``W*``) become ``clip-path``, and text
    (``BT``..``ET`` with ``Tf``, ``Td``, ``TD``, ``Tm``, ``T*``, ``Tj``,
    ``TJ``, ``'``, ``"``) becomes ``<text>`` in the font family named by the
    font, decoded as single-byte text. Axial and radial shadings (``sh`` and
    shading patterns) become linear and radial gradients, and tiling
    patterns become ``<pattern>`` elements. Blend modes, mesh shadings and
    ``/Rotate`` are ignored.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.formats.export._vector._pdf_read import read_pdf
    >>> doc = svg.Document(20, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> back = read_pdf(svg.export.export(doc, "pdf"))
    >>> back.root.get("width"), back[0].get("fill")
    (20.0, '#ff0000')
    """
    objects, pages = _document_pages(data)
    if not 0 <= page < len(pages):
        raise ValueError(f"page {page} out of range: the PDF file has {len(pages)} page(s)")
    leaf = pages[page]
    x0, y0, x1, y1 = _media_box(objects, leaf)
    painter = _Painter(objects, Matrix(PX_PER_PT, 0.0, 0.0, -PX_PER_PT, -x0 * PX_PER_PT, y1 * PX_PER_PT))
    width, height = (x1 - x0) * PX_PER_PT, (y1 - y0) * PX_PER_PT
    painter.page = [("M", (0.0, 0.0)), ("L", (width, 0.0)), ("L", (width, height)), ("L", (0.0, height)), ("Z", ())]
    resources = _inherited(objects, leaf, "Resources")
    painter.run(_content(objects, leaf), resources if isinstance(resources, dict) else {})
    return to_document(painter.shapes, (0.0, 0.0, width, height))


def page_count(data: bytes) -> int:
    """The number of pages in a PDF file.

    Parameters
    ----------
    data : bytes
        The PDF file.

    Returns
    -------
    int
        How many pages the page tree holds.

    Raises
    ------
    ValueError
        If *data* is not a readable PDF or has no pages.

    See Also
    --------
    read_pdf : Read one page.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.formats.export._vector._pdf_read import page_count
    >>> page_count(svg.export.export([svg.Document(5, 5)] * 3, "pdf"))
    3
    """
    return len(_document_pages(data)[1])


def _document_pages(data: bytes) -> tuple[dict[int, Any], list[dict[str, Any]]]:
    """The objects of a PDF file and its page leaves, checking that it can be read."""
    if PDF_HEADER not in data[:HEADER_WINDOW]:
        raise ValueError("not a PDF file: no '%PDF-' header")
    if ENCRYPT_RE.search(data):
        raise ValueError("encrypted PDF files are not supported")
    objects = _objects(data)
    pages = _pages(objects)
    if not pages:
        raise ValueError("no pages found in the PDF file")
    return objects, pages
