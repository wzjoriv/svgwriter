"""Presets of your own, by kind, each found by name.

Every kind is a registry: animations, behaviors, shapes, patterns, filters, gradients, markers and
effects register by decorator (bare, or with ``name=`` and ``replace=``) and sizes by a call
(``svg.preset.size(name, width, height)``); each has ``list()``, ``get(name)`` and ``unregister(name)``. A
taken name raises an error naming its owner, built-in presets included; ``replace=True`` replaces one on
purpose. Registered patterns, filters, gradients, markers and effects join their catalogues
(``svg.patterns``, ``svg.filters``, ``svg.gradients``, ``svg.markers``, ``svg.effects``) beside the
built-in ones. Packages add presets through the ``svgwriter.<kind>`` entry-point groups (see
:class:`~svgwriter.Registry`).

Example
-------
>>> import svgwriter as svg
>>> @svg.preset.animation
... def lift(motion: svg.Motion, *, height: float = 8) -> svg.Motion:
...     return motion.move_by(0, -height)
>>> _ = svg.rect(0, 0, 4, 4).animate.lift(height=2)
>>> "lift" in svg.preset.animation.list()
True
>>> _ = svg.preset.animation.unregister("lift")
"""

from __future__ import annotations

from typing import Final

from ..._internal._presets import (
    ANIMATIONS,
    BEHAVIORS,
    EFFECTS,
    FILTERS,
    GRADIENTS,
    KINDS,
    MARKERS,
    PATTERNS,
    SHAPES,
    SIZES,
    AnimationPresets,
    BehaviorPresets,
    DefinitionPresets,
    EffectPresets,
    ShapePresets,
    SizePresets,
)

animation: Final = ANIMATIONS
behavior: Final = BEHAVIORS
shape: Final = SHAPES
size: Final = SIZES
pattern: Final = PATTERNS
filter: Final = FILTERS  # noqa: A001
gradient: Final = GRADIENTS
marker: Final = MARKERS
effect: Final = EFFECTS

__all__ = [
    "KINDS",
    "AnimationPresets",
    "BehaviorPresets",
    "DefinitionPresets",
    "EffectPresets",
    "ShapePresets",
    "SizePresets",
    "animation",
    "behavior",
    "effect",
    "filter",
    "gradient",
    "marker",
    "pattern",
    "shape",
    "size",
]
