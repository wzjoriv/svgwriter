"""
Reading and writing files: SVG text, other formats and Inkscape documents.

Sub-packages
------------
export
    Format registry by name or extension: vector, raster, plotter, office
    and exchange formats; ``svg.export.register`` adds more.
io
    Serialization options, writers (string, file, stream, async) and the
    parser.
inkscape
    Inkscape files: layers, labels, editable stars and arcs, connectors,
    guides and export hints.

Notes
-----
The top-level package re-exports these, so ``svg.export`` and ``svg.parse``
work without this path. The group itself imports nothing.

Examples
--------
>>> from svgwriter.formats.io import to_string
>>> import svgwriter as svg
>>> to_string(svg.Rect(0, 0, 4, 4)).splitlines()[1]
'<rect x="0" y="0" width="4" height="4"/>'
"""
