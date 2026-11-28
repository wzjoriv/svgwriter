"""Ready-made gradients, used as paints: ``fill=svg.gradients.sunset()``.

Blends between distant colors are sampled in OKLCH, so they stay vivid where a plain sRGB blend turns
grey. Gradients are in bounding-box units, so one paint stretches to any shape; ``mesh`` is a pattern of
layered radial blends. Colors left to the theme come from :meth:`Theme.current <svgwriter.Theme.current>`
when the gradient is built. Gradients registered with :data:`svgwriter.library.preset.gradient` answer here too.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(80, 40)
>>> sky = doc.rect(0, 0, 80, 40, fill=svg.gradients.sunset())
>>> doc.root.defs()[0].tag
'linearGradient'
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._internal._presets import GRADIENTS, catalogue
from . import _library  # noqa: F401

if TYPE_CHECKING:
    from ._library import blend, iridescent, mesh, metallic, ocean, sunset, theme

__all__ = ["blend", "iridescent", "mesh", "metallic", "ocean", "sunset", "theme"]

GRADIENTS.seal()
__getattr__, __dir__ = catalogue(GRADIENTS, __name__)
