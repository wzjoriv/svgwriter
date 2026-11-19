"""Exporters and importers, discoverable by format name or file extension.

Built in: SVG, SVGZ, PNG, JPEG, WebP, PDF (vector, via skia), TikZ, EPS, DXF,
HPGL, G-code, Excalidraw, ICO and ICNS out; most of them in as well. Register more with :func:`register` and
:func:`register_importer`.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(20, 10)
>>> _ = doc.rect(0, 0, 20, 10, fill="teal")
>>> sorted(svg.export.exporters())
['dxf', 'eps', 'excalidraw', 'gcode', 'hpgl', 'icns', 'ico', 'jpeg', 'pdf', 'png', 'svg', 'svgz', 'tikz', 'webp']
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
]
