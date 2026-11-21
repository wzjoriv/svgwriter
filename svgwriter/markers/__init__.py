"""Ready-made markers for line ends and vertices: ``marker_end=svg.markers.arrow()``.

Markers are sized in stroke widths, so heads grow with the line, and turn with it (``orient="auto"``).
They take the line-end theme role ``"arrow.head"`` (the palette's foreground) unless a ``color=`` is given, and go into
the document's ``<defs>`` when a line refers to them. Markers registered with
:func:`svgwriter.preset.marker` answer here too.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(80, 20)
>>> line = doc.line(5, 10, 70, 10, stroke="black", stroke_width=2, marker_end=svg.markers.arrow())
>>> doc.root.defs()[0].tag
'marker'
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._internal._presets import MARKERS, catalogue
from . import _library  # noqa: F401

if TYPE_CHECKING:
    from ._library import arrow, bar, diamond, dot, open_arrow, square

__all__ = ["arrow", "bar", "diamond", "dot", "open_arrow", "square"]

MARKERS.seal()
__getattr__, __dir__ = catalogue(MARKERS, __name__)
