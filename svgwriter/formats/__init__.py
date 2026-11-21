"""
Reading and writing files: SVG text, other formats and Inkscape documents.

Sub-packages
------------
export
    Format registry by name or extension: vector, raster, plotter, office
    and exchange formats; a :class:`~svgwriter.Format` subclass adds more.
io
    Serialization options, writers (string, file, stream, async) and the
    parser.
inkscape
    Inkscape files: layers, labels, editable stars and arcs, connectors,
    guides and export hints.

The registry
------------
The package itself is the format registry, ``svg.formats``: ``list()``, ``get(name)``, ``register``,
``unregister(name)``, ``writer(path)``, ``reader(path)``, ``writers()`` and ``readers()``. A
:class:`~svgwriter.Format` subclass registers itself.

Notes
-----
The top-level package re-exports the sub-packages, so ``svg.export`` and ``svg.parse`` work without this
path.

Examples
--------
>>> from svgwriter.formats.io import to_string
>>> import svgwriter as svg
>>> to_string(svg.Rect(0, 0, 4, 4)).splitlines()[1]
'<rect x="0" y="0" width="4" height="4"/>'
>>> svg.formats.writer("figure.pdf").name, "svg" in svg.formats.readers()
('pdf', True)
"""

from __future__ import annotations

from ._format import FORMATS as _FORMATS
from ._format import Format, FormatRegistry

__all__ = ["Format", "FormatRegistry", "find", "get", "list", "reader", "readers", "register", "unregister", "writer", "writers"]

register = _FORMATS.register
list = _FORMATS.list  # noqa: A001
get = _FORMATS.get
find = _FORMATS.find
unregister = _FORMATS.unregister
writer = _FORMATS.writer
reader = _FORMATS.reader
writers = _FORMATS.writers
readers = _FORMATS.readers
