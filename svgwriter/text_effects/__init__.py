"""Text effects that stay text: ``svg.text_effects.fire(text[4:9])`` or ``text[4:9].effect("fire")``.

Each effect sets paint, a filter and, unless ``animate=False``, a small SMIL loop, so the effect plays in
browsers, GIFs and videos alike. The glyphs are never turned into outlines: the text stays selectable and
searchable. On a range, the characters move onto a copy of the text placed just above it (see
:meth:`CharacterRange.isolate <svgwriter.CharacterRange.isolate>`), so filters reach exactly those
characters; the text must already be in a document or group. Effects registered with
:func:`svgwriter.preset.text_effect` answer here too.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(300, 50)
>>> line = doc.text("Smoke and Snow", x=10, y=36, font_size=28)
>>> _ = svg.text_effects.smoke(line[0:5])
>>> _ = line[10:14].effect("snow")
>>> len(doc.root.find_all(svg.Text))
3
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._internal._presets import TEXT_EFFECTS, catalogue
from . import _elements, _materials  # noqa: F401

if TYPE_CHECKING:
    from ._elements import fire, ice, smoke, snow
    from ._materials import glitch, metal, neon, wind

__all__ = ["fire", "glitch", "ice", "metal", "neon", "smoke", "snow", "wind"]

TEXT_EFFECTS.seal()
__getattr__, __dir__ = catalogue(TEXT_EFFECTS, __name__)
