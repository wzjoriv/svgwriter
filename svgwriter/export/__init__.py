"""Exporters and importers, discoverable by format name or file extension.

Built in, out: SVG, SVGZ, PNG, JPEG, WebP, BMP, GIF, PPM, TIFF, PDF (vector, via skia), TikZ,
EPS, DXF, HPGL, G-code, Excalidraw, ICO and ICNS. In: SVG, SVGZ, raster images (PNG,
JPEG, WebP, GIF, BMP, PNM), PDF, TikZ and EPS (their vector paths), DXF, HPGL, G-code,
Excalidraw, ICO and ICNS, plus Graphviz DOT and Mermaid when their command-line
tools are installed; with the ``office`` extra, PPTX (editable shapes, in and out),
DOCX and XLSX (picture, out). Register more with :func:`register` and :func:`register_importer`.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(20, 10)
>>> _ = doc.rect(0, 0, 20, 10, fill="teal")
>>> {"svg", "png", "pdf", "tikz", "dxf"} <= set(svg.export.exporters())
True
>>> svg.export.export(doc, ".pdf")[:5]
b'%PDF-'
"""

from __future__ import annotations

from ._exchange import export, load, save
from ._registry import (
    Exporter,
    Importer,
    exporters,
    find_exporter,
    find_importer,
    importers,
    register,
    register_importer,
    unregister,
)

__all__ = [
    "Exporter",
    "Importer",
    "export",
    "exporters",
    "find_exporter",
    "find_importer",
    "importers",
    "load",
    "register",
    "register_importer",
    "save",
    "unregister",
]
