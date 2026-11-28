"""Inkscape documents: layers, labels, connectors, guides and export hints.

Files saved by Inkscape read and write back with their ``inkscape:`` and
``sodipodi:`` data intact; this package gives that data a Python interface. Editable stars and arcs
are native: see :class:`~svgwriter.library.paths.Star` and :class:`~svgwriter.library.paths.Arc`.
:class:`~svgwriter.Document` exposes the common parts directly
(``doc.layer``, ``doc.layers``, ``doc.guides``, ``doc.export_hints``).
"""

from __future__ import annotations

from .connectors import Connection, connect, connection
from .guides import Guide, guides, namedview, set_guides
from .hints import ExportHints, export_hints, set_export_hints
from .layers import by_label, is_layer, layers, new_layer

__all__ = [
    "Connection",
    "ExportHints",
    "Guide",
    "by_label",
    "connect",
    "connection",
    "export_hints",
    "guides",
    "is_layer",
    "layers",
    "namedview",
    "new_layer",
    "set_export_hints",
    "set_guides",
]
