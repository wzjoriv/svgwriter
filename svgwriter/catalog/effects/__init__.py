"""Effects for any element: ``svg.effects.fire(shape)``, ``element.effect("neon")`` or ``text[4:9].effect("ice")``.

Each effect sets paint, a filter and, unless ``animate=False``, a small SMIL loop, so the effect plays in
browsers, GIFs and videos alike. Effects size themselves to the element: a text to the height of its glyphs,
anything else to the shorter side of its bounding box. Text stays text, selectable and searchable. On a range
of a text, the characters move onto a copy of the text placed just above it (see
:meth:`CharacterRange.isolate <svgwriter.CharacterRange.isolate>`), so filters reach exactly those characters;
the text must already be in a document or group. Effects registered with :data:`svgwriter.preset.effect`
answer here too.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(300, 50)
>>> line = doc.text("Smoke and Snow", x=10, y=36, font_size=28)
>>> _ = svg.effects.smoke(line[0:5])
>>> _ = line[10:14].effect("snow")
>>> len(doc.root.find_all(svg.Text))
3
>>> doc.circle(270, 25, 15).effect("neon", color="deeppink").get("filter") is not None
True
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._internal._presets import EFFECTS, catalogue
from . import _elements, _materials  # noqa: F401

if TYPE_CHECKING:
    from ._elements import fire, ice, smoke, snow
    from ._materials import glitch, metal, neon, wind

__all__ = ["fire", "glitch", "ice", "metal", "neon", "smoke", "snow", "wind"]

EFFECTS.seal()
__getattr__, __dir__ = catalogue(EFFECTS, __name__)
