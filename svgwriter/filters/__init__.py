"""Ready-made filters: ``element.filter = svg.filters.glow(4)``.

Every function returns a :class:`~svgwriter.Filter` that goes into the document's ``<defs>`` when an element
refers to it, with a region enlarged so blurs and shadows are not clipped, computed in sRGB. Single
colors (shadows, outlines) default to theme roles (``"filter.shadow"``, ``"filter.ink"``), so they follow
the document theme. Filters registered with :func:`svgwriter.preset.filter` answer here too.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(80, 40)
>>> card = doc.rect(10, 10, 50, 20, fill="white", filter=svg.filters.drop_shadow(2, 3, 2))
>>> doc.root.defs()[0].tag
'filter'
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._internal._presets import FILTERS, catalogue
from . import _edges, _shadows, _surface  # noqa: F401

if TYPE_CHECKING:
    from ._edges import emboss, goo, outline
    from ._shadows import blur, drop_shadow, glow, inner_shadow, long_shadow
    from ._surface import bevel, duotone, grain, relief

__all__ = [
    "bevel",
    "blur",
    "drop_shadow",
    "duotone",
    "emboss",
    "glow",
    "goo",
    "grain",
    "inner_shadow",
    "long_shadow",
    "outline",
    "relief",
]

FILTERS.seal()
__getattr__, __dir__ = catalogue(FILTERS, __name__)
