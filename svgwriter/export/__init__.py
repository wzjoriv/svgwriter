"""Exporters and importers, discoverable by format name or file extension.

Built in, out: SVG, SVGZ, PNG, JPEG, WebP, BMP, GIF, PPM, PDF (vector, via skia), TikZ,
EPS, DXF, HPGL, G-code, Excalidraw, ICO and ICNS. In: SVG, SVGZ, raster images (PNG,
JPEG, WebP, GIF, BMP, PNM), PDF, TikZ and EPS (their vector paths), DXF, HPGL, G-code,
Excalidraw, ICO and ICNS. Register more with :func:`register` and :func:`register_importer`.

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

from ._registry import (
    Exporter,
    Importer,
    export,
    exporters,
    find_exporter,
    find_importer,
    importers,
    load,
    register,
    register_importer,
    save,
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
