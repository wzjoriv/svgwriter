"""Presets of your own, by kind, each found by name.

Every kind is a registry: animations, behaviors, shapes, patterns, filters, gradients, markers,
effects, interactions, path effects and interpolators register by decorator (bare, or with ``name=`` and ``replace=``), sizes by a call
(``svg.preset.size(name, width, height)``) and fonts by a call with files or folders (``svg.preset.font(path)``); each has ``list()``, ``get(name)`` and ``unregister(name)``. A
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
    FONTS,
    GRADIENTS,
    INTERACTIONS,
    INTERPOLATORS,
    KINDS,
    MARKERS,
    PATH_EFFECTS,
    PATTERNS,
    SHAPES,
    SIZES,
    AnimationPresets,
    BehaviorPresets,
    DefinitionPresets,
    EffectPresets,
    FontPresets,
    InteractionPresets,
    InterpolatorPresets,
    PathEffectPresets,
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
interaction: Final = INTERACTIONS
path_effect: Final = PATH_EFFECTS
interpolator: Final = INTERPOLATORS
font: Final = FONTS

__all__ = [
    "KINDS",
    "AnimationPresets",
    "BehaviorPresets",
    "DefinitionPresets",
    "EffectPresets",
    "FontPresets",
    "InteractionPresets",
    "InterpolatorPresets",
    "PathEffectPresets",
    "ShapePresets",
    "SizePresets",
    "animation",
    "behavior",
    "effect",
    "filter",
    "font",
    "gradient",
    "interaction",
    "interpolator",
    "marker",
    "path_effect",
    "pattern",
    "shape",
    "size",
]
