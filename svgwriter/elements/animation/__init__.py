"""
SMIL animation elements (``animate``, ``set``, ``animateMotion``, ``mpath``, ``animateColor``,
``animateTransform``) and their timing curve, ``Ease``.
"""

from __future__ import annotations

from ._easing import Ease, EaseLike
from ._elements import (
    Accumulate,
    Additive,
    Animate,
    AnimateColor,
    AnimateMotion,
    AnimateTransform,
    AnimationElement,
    AnimationFill,
    CalcMode,
    MPath,
    Restart,
    Set,
    TransformType,
)

__all__ = [
    "Accumulate",
    "Additive",
    "Animate",
    "AnimateColor",
    "AnimateMotion",
    "AnimateTransform",
    "AnimationElement",
    "AnimationFill",
    "CalcMode",
    "Ease",
    "EaseLike",
    "MPath",
    "Restart",
    "Set",
    "TransformType",
]
