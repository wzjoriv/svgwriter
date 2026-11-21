"""
Exporting, saving and loading documents through the registered formats.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._registry import Exporter, find_exporter, find_importer

if TYPE_CHECKING:
    from ..document import Document

__all__ = ["export", "load", "save"]


def export(document: Document | Sequence[Document], format: str, *, seconds: float | None = None,
           **options: Any) -> bytes | str:
    """Convert *document* to *format* (a name or extension); returns ``bytes`` or ``str``.

    Parameters
    ----------
    document : Document or sequence of Document
        The document to convert, or several documents for a multi-page format
        (``"pdf"``: one page each; ``"pptx"``: one slide each).
    format : str
        A registered format name or an extension such as ``".pdf"``.
    seconds : float, optional
        Export the SMIL animation frame at this many seconds (see
        :meth:`Document.at`) instead of the document as written. Defaults to
        None, which keeps animations (formats without animation show t = 0).
    **options
        Passed to the exporter function (see each format's description in :func:`exporters`).

    Returns
    -------
    bytes or str
        The file contents; text formats return ``str``.

    Raises
    ------
    ValueError
        If no exporter matches *format*, the sequence is empty, or several
        documents are given to a single-page format.

    See Also
    --------
    save : Write the result to a file.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(4, 4)
    >>> svg.export.export(doc, "png")[:4] == bytes.fromhex("89504e47")
    True
    >>> deck = svg.export.export([doc, svg.Document(8, 2)], "pdf")
    >>> len(svg.export.find_importer("pdf").function(deck, page=None))
    2
    """
    exporter = find_exporter(format)
    return exporter.function(_frames(exporter, document, seconds), **options)


def _frames(exporter: Exporter, document: Document | Sequence[Document], seconds: float | None) -> Any:
    """The document (or list of documents) to hand to *exporter*, at *seconds* when given."""
    if isinstance(document, Sequence):
        if not document:
            raise ValueError("no documents to export")
        if not exporter.multipage:
            raise ValueError(f"the {exporter.name} format holds one document; "
                             f"export several to a multi-page format such as pdf or pptx")
        return [page.at(seconds) if seconds is not None else page for page in document]
    return document.at(seconds) if seconds is not None else document


def save(document: Document | Sequence[Document], path: str | os.PathLike[str], format: str | None = None, *,
         seconds: float | None = None, **options: Any) -> Path:
    """Write *document* to *path*, choosing the format from *format* or the file extension.

    Parameters
    ----------
    document : Document or sequence of Document
        The document to write, or several for a multi-page format (one PDF
        page or PowerPoint slide each).
    path : str or path-like
        Destination file.
    format : str, optional
        Format name overriding the extension. Defaults to None.
    seconds : float, optional
        Save the SMIL animation frame at this many seconds instead of the
        animated document. Defaults to None.
    **options
        Passed to the exporter function.

    Returns
    -------
    pathlib.Path
        The file that was written.

    Raises
    ------
    ValueError
        If no exporter matches, or several documents are given to a
        single-page format.

    See Also
    --------
    export : Get the contents without writing a file.
    load : Read a document back.

    Examples
    --------
    >>> import tempfile
    >>> from pathlib import Path
    >>> import svgwriter as svg
    >>> with tempfile.TemporaryDirectory() as folder:
    ...     target = svg.export.save(svg.Document(4, 4), Path(folder) / "a.svg")
    ...     target.read_text(encoding="utf-8").startswith("<?xml")
    True
    """
    exporter = find_exporter(format or path)
    data = exporter.function(_frames(exporter, document, seconds), **options)
    target = Path(path)
    if isinstance(data, bytes):
        target.write_bytes(data)
    else:
        target.write_text(data, encoding="utf-8", newline="\n")
    return target


def load(path: str | os.PathLike[str], format: str | None = None, **options: Any) -> Document | list[Document]:
    """Read a document from *path* with the importer chosen by *format* or the extension.

    Parameters
    ----------
    path : str or path-like
        The file to read.
    format : str, optional
        Format name overriding the extension. Defaults to None.
    **options
        Passed to the importer function.

    Returns
    -------
    Document or list of Document
        The parsed document; relative image links inside it resolve against
        *path*. Multi-page formats return a list, one document per page, when
        their page option is None (``page=None`` for PDF, ``slide=None`` for
        PowerPoint).

    Raises
    ------
    ValueError
        If no importer matches.

    See Also
    --------
    save : Write a document.
    Document.open_all : Every page of a file as a list.

    Examples
    --------
    >>> import tempfile
    >>> from pathlib import Path
    >>> import svgwriter as svg
    >>> with tempfile.TemporaryDirectory() as folder:
    ...     target = svg.export.save(svg.Document(4, 4), Path(folder) / "a.svg")
    ...     svg.export.load(target).root.tag
    'svg'
    """
    importer = find_importer(format or path)
    result = importer.function(Path(path).read_bytes(), **options)
    for document in result if isinstance(result, list) else [result]:
        document.root._source_path = os.fspath(path)
    return result
