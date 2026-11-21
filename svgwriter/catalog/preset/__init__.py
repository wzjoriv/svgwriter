"""Presets of your own, by kind, each found by name.

Animations, behaviors, shapes, patterns, filters, gradients, markers and text effects register by
decorator (``name=``, ``replace=``) and sizes by a call (``svg.preset.size(name, width, height)``); every
kind has ``list(kind)``, ``get(kind, name)`` and ``unregister(kind, name)``. A taken name raises an error
naming its owner, built-in presets included; ``replace=True`` replaces one on purpose. Registered
patterns, filters, gradients, markers and text effects join their catalogues (``svg.patterns``,
``svg.filters``, ``svg.gradients``, ``svg.markers``, ``svg.text_effects``) beside the built-in ones.

Example
-------
>>> import svgwriter as svg
>>> @svg.preset.animation
... def lift(motion: svg.Motion, *, height: float = 8) -> svg.Motion:
...     return motion.move_by(0, -height)
>>> _ = svg.rect(0, 0, 4, 4).animate.lift(height=2)
>>> "lift" in svg.preset.list("animation")
True
>>> svg.preset.unregister("animation", "lift")
"""

from __future__ import annotations

from ._animation import animation
from ._behavior import behavior
from ._catalogue import filter, gradient, marker, pattern
from ._kinds import get, list, unregister
from ._shape import shape
from ._size import size
from ._text_effect import text_effect

__all__ = [
    "animation",
    "behavior",
    "filter",
    "get",
    "gradient",
    "list",
    "marker",
    "pattern",
    "shape",
    "size",
    "text_effect",
    "unregister",
]
