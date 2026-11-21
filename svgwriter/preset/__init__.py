"""Presets of your own, by kind: animations, behaviors, shapes and canvas sizes, each found by name.

Animations and shapes register by decorator (``name=``, ``replace=``) and sizes by a call
(``svg.preset.size(name, width, height)``); every kind has ``list(kind)``, ``get(kind, name)`` and
``unregister(kind, name)``. A taken name raises an error naming its
owner, built-in presets included; ``replace=True`` replaces one on purpose.

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
from ._kinds import get, list, unregister
from ._shape import shape
from ._size import size

__all__ = ["animation", "behavior", "get", "list", "shape", "size", "unregister"]
