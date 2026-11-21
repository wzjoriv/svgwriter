"""Presets of your own, by kind: animations, behaviors and shapes, each registered by a decorator and found by name.

Every kind has the same API: a decorator that registers a function (``name=``, ``replace=``), and
``list(kind)``, ``get(kind, name)`` and ``unregister(kind, name)``. A taken name raises an error naming its
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

__all__ = ["animation", "behavior", "get", "list", "shape", "unregister"]
