"""
Office files through the optional ``svgwriter[office]`` extra: PowerPoint shapes out and in, Word and Excel pictures out.
"""

from __future__ import annotations

import importlib
import io
from typing import TYPE_CHECKING, Any, Final

from .._registry import register, register_importer

if TYPE_CHECKING:
    from ...document import Document

__all__ = ["OfficeExtraError"]

EXTRA_HINT: Final = "pip install 'svgwriter[office]'"
PICTURE_SCALE: Final = 2.0


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


@register("pptx", extensions=(".pptx",))
def pptx(document: Document) -> bytes:
    """A PowerPoint deck with one slide holding the drawing as editable shapes.

    Every painted outline becomes a freeform shape with its curves, solid
    fill, outline and transparency; embedded images become pictures.

    Parameters
    ----------
    document : Document
        The drawing.

    Returns
    -------
    bytes
        The ``.pptx`` file.

    Raises
    ------
    OfficeExtraError
        If ``python-pptx`` is not installed.

    Notes
    -----
    Gradients and patterns become their first color, as in the other vector
    exports; pictures sit below the shapes.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(40, 20)
    >>> _ = doc.rect(0, 0, 40, 20, fill="teal")
    >>> svg.export.export(doc, "pptx")[:2]
    b'PK'
    """
    from ._pptx import write_pptx

    return write_pptx(document)


@register_importer("pptx", extensions=(".pptx",))
def read_pptx(data: bytes, *, slide: int = 0) -> Document:
    """One slide of a PowerPoint deck as native SVG elements.

    Freeform and preset shapes (rectangles, rounded rectangles, ellipses,
    lines) become paths with their solid fill and outline, pictures become
    images and text boxes become text.

    Parameters
    ----------
    data : bytes
        The ``.pptx`` file.
    slide : int, optional
        Zero-based slide number. Defaults to 0.

    Returns
    -------
    Document
        The slide, sized like it.

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
    from ._pptx import read_pptx as read

    return read(data, slide)


def _picture(document: Document) -> tuple[bytes, float, float]:
    """The drawing as PNG bytes plus its size in inches at 96 user units per inch."""
    from ...ops.render import document_size

    width, height = document_size(document)
    png = document.export("png", scale=PICTURE_SCALE)
    return png, width / USER_UNITS_PER_INCH, height / USER_UNITS_PER_INCH


USER_UNITS_PER_INCH: Final = 96.0


@register("docx", extensions=(".docx",))
def docx(document: Document) -> bytes:
    """A Word document holding the drawing as a picture at its natural size.

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

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(40, 20), "docx")[:2]
    b'PK'
    """
    word = require("docx")
    shared = require("docx.shared")
    png, width, height = _picture(document)
    out = word.Document()
    out.add_picture(io.BytesIO(png), width=shared.Inches(width), height=shared.Inches(height))
    buffer = io.BytesIO()
    out.save(buffer)
    return buffer.getvalue()


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
    """The pictures and drawn shapes of a Word document as elements.

    Floating (anchored) items keep their page position; inline ones stack
    down the page in document order. Text is not imported.

    Parameters
    ----------
    data : bytes
        The ``.docx`` file.

    Returns
    -------
    Document
        Images and paths, sized to fit.

    Raises
    ------
    OfficeExtraError
        If ``python-docx`` is not installed.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(40, 20)
    >>> _ = doc.rect(0, 0, 40, 20, fill="teal")
    >>> back = svg.export.find_importer("docx").function(svg.export.export(doc, "docx"))
    >>> [e.tag for e in back]
    ['image']
    """
    from ._docx import read_docx as read

    return read(data)
