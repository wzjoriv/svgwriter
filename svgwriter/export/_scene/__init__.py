"""
Excalidraw scenes, out and in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._registry import register, register_importer

if TYPE_CHECKING:
    from ...document import Document


@register("excalidraw", extensions=(".excalidraw",), binary=False)
def excalidraw(document: Document, **options: Any) -> str:
    """Excalidraw scene JSON (outlines as line elements).

    Parameters
    ----------
    document : Document
        The document to convert.
    **options
        Keyword options of :func:`~svgwriter.export._scene._excalidraw.to_excalidraw`.

    Returns
    -------
    str
        The scene as JSON text.

    See Also
    --------
    read_excalidraw : Read a scene back.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.export(svg.Document(4, 4), "excalidraw").count("excalidraw") > 0
    True
    """
    from ._excalidraw import to_excalidraw

    return to_excalidraw(document, **options)


@register_importer("excalidraw", extensions=(".excalidraw", ".json"))
def read_excalidraw(data: bytes) -> Document:
    """Excalidraw scene JSON as native SVG shapes, text and images.

    Parameters
    ----------
    data : bytes
        The scene JSON, UTF-8 encoded.

    Returns
    -------
    Document
        The drawing as a document.

    See Also
    --------
    excalidraw : Write a scene.

    Examples
    --------
    >>> import svgwriter as svg
    >>> data = svg.export.export(svg.Document(4, 4), "excalidraw").encode()
    >>> svg.export.find_importer(".excalidraw").function(data).root.tag
    'svg'
    """
    from ._excalidraw import read_excalidraw as read

    return read(data.decode("utf-8"))
