"""
CNC and plotter formats: DXF, HPGL and G-code, out and in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._registry import register, register_importer

if TYPE_CHECKING:
    from ....document import Document


@register("dxf", extensions=(".dxf",), binary=False)
def dxf(document: Document, **options: Any) -> str:
    """AutoCAD DXF R12 polylines in mm (``tolerance``, ``unit_mm``).

    Parameters
    ----------
    document : Document
        The document to convert.
    **options
        ``tolerance`` and ``unit_mm``, as for :func:`~svgwriter.formats.export._plotter._cnc.to_dxf`.

    Returns
    -------
    str
        DXF text.

    See Also
    --------
    read_dxf : Read DXF back.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> "POLYLINE" in svg.export.export(doc, "dxf")
    True
    """
    from ._cnc import to_dxf

    return to_dxf(document, **options)


@register("hpgl", extensions=(".hpgl", ".plt"), binary=False)
def hpgl(document: Document, **options: Any) -> str:
    """HPGL for pen plotters and vinyl cutters, one pen per colour (``tolerance``, ``unit_mm``).

    Parameters
    ----------
    document : Document
        The document to convert.
    **options
        ``tolerance`` and ``unit_mm``, as for :func:`~svgwriter.formats.export._plotter._cnc.to_hpgl`.

    Returns
    -------
    str
        HPGL text.

    See Also
    --------
    read_hpgl : Read HPGL back.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> svg.export.export(doc, "hpgl").startswith("IN;")
    True
    """
    from ._cnc import to_hpgl

    return to_hpgl(document, **options)


@register("gcode", extensions=(".gcode", ".nc", ".ngc"), binary=False)
def gcode(document: Document, **options: Any) -> str:
    """G-code toolpaths for CNC mills and lasers (``feed``, ``mode``, ``cut_z``, ``tolerance``, ...).

    Parameters
    ----------
    document : Document
        The document to convert.
    **options
        Keyword options of :func:`~svgwriter.formats.export._plotter._cnc.to_gcode`.

    Returns
    -------
    str
        G-code text.

    See Also
    --------
    read_gcode : Read G-code back.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> svg.export.export(doc, "gcode", mode="laser").startswith("G21")
    True
    """
    from ._cnc import to_gcode

    return to_gcode(document, **options)


@register_importer("dxf", extensions=(".dxf",))
def read_dxf(data: bytes, **options: Any) -> Document:
    """DXF lines, polylines, circles, arcs and ellipses as stroked paths.

    Parameters
    ----------
    data : bytes
        The DXF text, UTF-8 encoded.
    **options
        ``unit_mm``, as for :func:`~svgwriter.formats.export._plotter._cnc_read.read_dxf`.

    Returns
    -------
    Document
        A document with one stroked path per entity.

    See Also
    --------
    dxf : Write DXF.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> data = svg.export.export(doc, "dxf").encode()
    >>> len(svg.export.find_importer(".dxf").function(data)) > 0
    True
    """
    from ._cnc_read import read_dxf as read

    return read(data.decode("utf-8", "replace"), **options)


@register_importer("hpgl", extensions=(".hpgl", ".plt"))
def read_hpgl(data: bytes, **options: Any) -> Document:
    """HPGL pen moves as stroked paths, coloured by pen.

    Parameters
    ----------
    data : bytes
        The HPGL text, ASCII encoded.
    **options
        ``unit_mm``, as for :func:`~svgwriter.formats.export._plotter._cnc_read.read_hpgl`.

    Returns
    -------
    Document
        A document with one stroked path per pen-down run.

    See Also
    --------
    hpgl : Write HPGL.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> data = svg.export.export(doc, "hpgl").encode()
    >>> len(svg.export.find_importer(".hpgl").function(data)) > 0
    True
    """
    from ._cnc_read import read_hpgl as read

    return read(data.decode("ascii", "replace"), **options)


@register_importer("gcode", extensions=(".gcode", ".nc", ".ngc"))
def read_gcode(data: bytes, **options: Any) -> Document:
    """G-code cutting moves as stroked paths.

    Parameters
    ----------
    data : bytes
        The G-code text, ASCII encoded.
    **options
        ``unit_mm``, as for :func:`~svgwriter.formats.export._plotter._cnc_read.read_gcode`.

    Returns
    -------
    Document
        A document with one stroked path per cutting run.

    See Also
    --------
    gcode : Write G-code.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> data = svg.export.export(doc, "gcode").encode()
    >>> len(svg.export.find_importer(".gcode").function(data)) > 0
    True
    """
    from ._cnc_read import read_gcode as read

    return read(data.decode("ascii", "replace"), **options)
