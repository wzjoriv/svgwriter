"""File formats, found by name or file extension, and the functions that export, save and load through them.

Built in, out: SVG, SVGZ, PNG, JPEG, WebP, BMP, GIF, PPM, TIFF, PDF (vector, via skia), TikZ,
EPS, DXF, HPGL, G-code, Excalidraw, HTML, ICO and ICNS. In: SVG, SVGZ, raster images (PNG,
JPEG, WebP, GIF, BMP, PNM), PDF, TikZ and EPS (their vector paths), DXF, HPGL, G-code,
Excalidraw, HTML, ICO and ICNS, text and Markdown, plus Graphviz DOT, Mermaid, PlantUML and D2
when their command-line tools are installed; with the ``office`` extra, PPTX (editable shapes,
in and out), DOCX (in and out) and XLSX (picture, out). Add a format by subclassing
:class:`~svgwriter.Format`; ``svg.formats`` lists them.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(20, 10)
>>> _ = doc.rect(0, 0, 20, 10, fill="teal")
>>> {"svg", "png", "pdf", "tikz", "dxf"} <= set(svg.formats.list())
True
>>> svg.export.export(doc, ".pdf")[:5]
b'%PDF-'
"""

from __future__ import annotations

from ._exchange import export, load, save

__all__ = ["export", "load", "load_formats", "save"]


def load_formats() -> None:
    """Import the built-in formats, so they register; the format registry calls it before its first lookup.

    Examples
    --------
    >>> from svgwriter.formats.export import load_formats
    >>> load_formats()
    """
    from . import _diagram, _html, _office, _plotter, _raster, _scene, _svg, _text, _vector  # noqa: F401
