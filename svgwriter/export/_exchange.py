"""
Exporting, saving and loading documents through the registered formats.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._registry import find_exporter, find_importer

if TYPE_CHECKING:
    from ..document import Document

__all__ = ["export", "load", "save"]


def export(document: Document, format: str, *, time: float | None = None, **options: Any) -> bytes | str:
    """Convert *document* to *format* (a name or extension); returns ``bytes`` or ``str``.

    Parameters
    ----------
    document : Document
        The document to convert.
    format : str
        A registered format name or an extension such as ``".pdf"``.
    time : float, optional
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
        If no exporter matches *format*.

    See Also
    --------
    save : Write the result to a file.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(4, 4)
    >>> svg.export.export(doc, "png")[:4] == bytes.fromhex("89504e47")
    True
    """
    exporter = find_exporter(format)
    return exporter.function(document.at(time) if time is not None else document, **options)


def save(document: Document, path: str | os.PathLike[str], format: str | None = None, *, time: float | None = None,
    **options: Any) -> Path:
    """Write *document* to *path*, choosing the format from *format* or the file extension.

    Parameters
    ----------
    document : Document
        The document to write.
    path : str or path-like
        Destination file.
    format : str, optional
        Format name overriding the extension. Defaults to None.
    time : float, optional
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
        If no exporter matches.

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
    data = exporter.function(document.at(time) if time is not None else document, **options)
    target = Path(path)
    if isinstance(data, bytes):
        target.write_bytes(data)
    else:
        target.write_text(data, encoding="utf-8", newline="\n")
    return target


def load(path: str | os.PathLike[str], format: str | None = None, **options: Any) -> Document:
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
    Document
        The parsed document; relative image links inside it resolve against *path*.

    Raises
    ------
    ValueError
        If no importer matches.

    See Also
    --------
    save : Write a document.

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
    document = importer.function(Path(path).read_bytes(), **options)
    document.root._source_path = os.fspath(path)
    return document
