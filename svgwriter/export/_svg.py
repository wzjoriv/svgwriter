"""
SVG and gzip-compressed SVGZ, out and in.
"""

from __future__ import annotations

import gzip
from typing import TYPE_CHECKING, Any, Final

from ._registry import register, register_importer

if TYPE_CHECKING:
    from ..document import Document

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
