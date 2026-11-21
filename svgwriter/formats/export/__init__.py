"""File formats, found by name or file extension, and the functions that export, save and load through them.

Built in, out: SVG, SVGZ, PNG, JPEG, WebP, BMP, GIF, PPM, TIFF, PDF (vector, via skia), TikZ,
EPS, DXF, HPGL, G-code, Excalidraw, HTML, ICO and ICNS. In: SVG, SVGZ, raster images (PNG,
JPEG, WebP, GIF, BMP, PNM), PDF, TikZ and EPS (their vector paths), DXF, HPGL, G-code,
Excalidraw, HTML, ICO and ICNS, text and Markdown, plus Graphviz DOT, Mermaid, PlantUML and D2
when their command-line tools are installed; with the ``office`` extra, PPTX (editable shapes,
in and out), DOCX (in and out) and XLSX (picture, out). Add a format by subclassing
:class:`Format`; :data:`FORMATS` lists them.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(20, 10)
>>> _ = doc.rect(0, 0, 20, 10, fill="teal")
>>> {"svg", "png", "pdf", "tikz", "dxf"} <= set(svg.FORMATS.list())
True
>>> svg.export.export(doc, ".pdf")[:5]
b'%PDF-'
"""

from __future__ import annotations

from ._exchange import export, load, save
from ._format import FORMATS, Format, FormatRegistry

__all__ = ["FORMATS", "Format", "FormatRegistry", "export", "load", "save"]
