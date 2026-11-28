"""Ready-made patterns, used as paints: ``fill=svg.patterns.stripes(angle=45, gap=6)``.

Every pattern returns a :class:`~svgwriter.Pattern` in user units that goes into the document's
``<defs>`` when an element refers to it. Shapes take the theme role ``"pattern"`` (the palette's primary
color) unless a ``color=`` or another ``role=`` is given; ``background=`` fills behind them. Patterns
registered with :data:`svgwriter.library.preset.pattern` answer here too, and a built-in replaced with
``replace=True`` answers with the replacement.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(60, 40)
>>> box = doc.rect(0, 0, 60, 40, fill=svg.patterns.hatch(gap=4, color="slategray"))
>>> doc.root.defs()[0].tag
'pattern'
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._internal._presets import PATTERNS, catalogue
from . import _geometric, _organic  # noqa: F401

if TYPE_CHECKING:
    from ._geometric import checker, crosshatch, dots, grid, hatch, stripes
    from ._organic import noise, waves, zigzag

__all__ = ["checker", "crosshatch", "dots", "grid", "hatch", "noise", "stripes", "waves", "zigzag"]

PATTERNS.seal()
__getattr__, __dir__ = catalogue(PATTERNS, __name__)
