"""
Office files through the optional ``pysvgwriter[office]`` extra: PowerPoint and Word shapes and text out and in, Excel pictures out.
"""

from __future__ import annotations

import importlib
import io
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from .._registry import register, register_importer
from ._constants import EXTRA_HINT, PICTURE_SCALE, USER_UNITS_PER_INCH

if TYPE_CHECKING:
    from ...document import Document

__all__ = ["OfficeExtraError"]


class OfficeExtraError(ImportError):
    """The library for an Office format is not installed.

    Examples
    --------
    >>> from svgwriter.export._office import OfficeExtraError
    >>> issubclass(OfficeExtraError, ImportError)
    True
    """


def require(module: str) -> Any:
    """Import *module* from the office extra, or explain how to install it."""
    try:
        return importlib.import_module(module)
    except ImportError as error:
        raise OfficeExtraError(f"{module.split('.')[0]} is needed for this format; {EXTRA_HINT}") from error


@register("pptx", extensions=(".pptx",), multipage=True)
def pptx(document: Document | Sequence[Document]) -> bytes:
    """A PowerPoint deck with one slide per drawing, as editable shapes.

    Every painted outline becomes a freeform shape with its curves, solid
    fill, outline and transparency; embedded images become pictures, and
    formulas made by :func:`svgwriter.latex` become editable equations
    (outlines when the LaTeX has no Office equivalent).

    Parameters
    ----------
    document : Document or sequence of Document
        The drawing, or several drawings for one slide each. A deck has a
        single slide size, so it fits the widest and tallest drawing and
        smaller drawings are centred on their slides.

    Returns
    -------
    bytes
        The ``.pptx`` file.

    Raises
    ------
    OfficeExtraError
        If ``python-pptx`` is not installed.

    Warns
    -----
    UserWarning
        Once, listing the SMIL animations PowerPoint cannot play.

    Notes
    -----
    Patterns become their tiles, as in the other vector exports; pictures keep
    their place among the shapes. SMIL animations become slide effects that
    start with the slide at their own ``begin``: fades, show and hide, motion
    (translations and paths), rotation, scale and fill or stroke colour
    changes, with duration, repeats and an approximated ease. Shapes with an
    entrance effect are drawn visible, as PowerPoint hides them until it plays.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(40, 20)
    >>> _ = doc.rect(0, 0, 40, 20, fill="teal")
    >>> svg.export.export(doc, "pptx")[:2]
    b'PK'
    >>> deck = svg.export.export([doc, svg.Document(20, 20)], "pptx")
    >>> len(svg.export.find_importer("pptx").function(deck, slide=None))
    2
    """
    from ._pptx import write_pptx

    return write_pptx(list(document) if isinstance(document, Sequence) else [document])


@register_importer("pptx", extensions=(".pptx",), page_option="slide")
def read_pptx(data: bytes, *, slide: int | None = 0) -> Document | list[Document]:
    """The slides of a PowerPoint deck as native SVG elements.

    Freeform and preset shapes (rectangles, rounded rectangles, ellipses,
    lines) become paths with their solid fill and outline, pictures become
    images and text boxes become text, and slide effects (fades, appear and
    disappear, motion paths, spins, grow and shrink, colour changes) become
    ``element.animate`` presets timed from the start of the slide, click
    steps following one another.

    Parameters
    ----------
    data : bytes
        The ``.pptx`` file.
    slide : int or None, optional
        Zero-based slide number, or None for every slide. Defaults to 0.

    Returns
    -------
    Document or list of Document
        The slide, sized like it; a list with one per slide when *slide* is None.

    Raises
    ------
    OfficeExtraError
        If ``python-pptx`` is not installed.
    IndexError
        If the deck has no such slide.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(40, 20)
    >>> _ = doc.circle(20, 10, 8, fill="red")
    >>> back = svg.export.find_importer("pptx").function(svg.export.export(doc, "pptx"))
    >>> [e.tag for e in back]
    ['path']
    """
    from ._pptx_read import read_pptx as read

    return read(data, slide)


def _picture(document: Document) -> tuple[bytes, float, float]:
    """The drawing as PNG bytes plus its size in inches at 96 user units per inch."""
    from ...ops.render import document_size

    width, height = document_size(document)
    png = document.export("png", scale=PICTURE_SCALE)
    return png, width / USER_UNITS_PER_INCH, height / USER_UNITS_PER_INCH


@register("docx", extensions=(".docx",))
def docx(document: Document) -> bytes:
    """A Word document holding the drawing as native, editable Word shapes at its natural size.

    Every painted outline becomes a floating freeform shape with its curves,
    solid or gradient fill, outline and transparency; images become
    pictures and text runs become borderless text boxes. They float in one
    paragraph whose line is as tall as the drawing, so text after it
    starts below. Formulas made by :func:`svgwriter.latex` become editable
    Word equations where they were drawn, or equation paragraphs when the
    drawing holds nothing else.

    Parameters
    ----------
    document : Document
        The drawing.

    Returns
    -------
    bytes
        The ``.docx`` file.

    Raises
    ------
    OfficeExtraError
        If ``python-docx`` is not installed.

    Notes
    -----
    The drawing is flattened as for PowerPoint: patterns, clipping and
    markers are drawn into the shapes, masks and filters are skipped, and
    pictures are placed by their upright bounding box.

    Examples
    --------
    >>> import io, zipfile
    >>> import svgwriter as svg
    >>> doc = svg.Document(40, 20)
    >>> _ = doc.rect(0, 0, 40, 20, fill="teal")
    >>> data = svg.export.export(doc, "docx")
    >>> b"<wps:wsp>" in zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml")
    True
    """
    from ._docx import write_docx

    return write_docx(document)


@register("xlsx", extensions=(".xlsx",))
def xlsx(document: Document) -> bytes:
    """An Excel workbook with the drawing as a picture anchored at cell A1.

    Parameters
    ----------
    document : Document
        The drawing.

    Returns
    -------
    bytes
        The ``.xlsx`` file.

    Raises
    ------
    OfficeExtraError
        If ``openpyxl`` (with Pillow) is not installed.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(40, 20), "xlsx")[:2]
    b'PK'
    """
    workbook_module = require("openpyxl")
    drawing = require("openpyxl.drawing.image")
    png, _, _ = _picture(document)
    book = workbook_module.Workbook()
    picture = drawing.Image(io.BytesIO(png))
    picture.width, picture.height = picture.width / PICTURE_SCALE, picture.height / PICTURE_SCALE
    book.active.add_image(picture, "A1")
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


@register_importer("docx", extensions=(".docx",))
def read_docx(data: bytes) -> Document:
    """A Word document as live text laid out top to bottom, with its pictures and drawn shapes.

    Paragraphs become ``<text>`` lines stacked like the Markdown importer:
    ``Title`` and ``Heading 1``-``6`` paragraphs are bold at the heading
    sizes, bulleted and numbered list paragraphs get a bullet or their
    number indented by list level, and line breaks start new lines. Each
    run's bold, italics, underline, strike-through, size, colour and font
    become a styled ``<tspan>``. Inline pictures and shapes take their
    place in the flow; floating (anchored) ones keep their offset, and
    the text of floating text boxes comes back where the box sat.

    Parameters
    ----------
    data : bytes
        The ``.docx`` file.

    Returns
    -------
    Document
        A group of text and inline figures plus the floating items, sized to fit.

    Raises
    ------
    OfficeExtraError
        If ``python-docx`` is not installed.

    Notes
    -----
    Lines are not re-wrapped, and tables are read cell by cell as
    paragraphs. Styles are read from the paragraph's own style name and
    the run's direct formatting, not from the style definitions.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(40, 20)
    >>> _ = doc.rect(0, 0, 40, 20, fill="teal")
    >>> back = svg.export.find_importer("docx").function(svg.export.export(doc, "docx"))
    >>> [e.tag for e in back]
    ['path']
    """
    from ._docx_read import read_docx as read

    return read(data)
