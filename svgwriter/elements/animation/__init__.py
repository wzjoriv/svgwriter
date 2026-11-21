"""
SMIL animation elements (``animate``, ``set``, ``animateMotion``, ``mpath``, ``animateColor``,
``animateTransform``) and their timing curve, ``Ease``.
"""

from __future__ import annotations

from ._easing import Ease, EaseLike
from ._elements import (
    Animate,
    AnimateColor,
    AnimateMotion,
    AnimateTransform,
    AnimationElement,
    MPath,
    Set,
)
from ._keywords import Accumulate, Additive, AnimationFill, CalcMode, Restart, TransformType

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
