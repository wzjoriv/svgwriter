"""
SMIL animation elements (``animate``, ``set``, ``animateMotion``, ``mpath``, ``animateColor``,
``animateTransform``) and their timing curve, ``Ease``.
"""

from __future__ import annotations

from ._color_transform import AnimateColor, AnimateTransform
from ._easing import Ease, EaseLike
from ._elements import Animate, AnimationElement, Set
from ._keywords import Accumulate, Additive, AnimationFill, CalcMode, Restart, TransformType
from ._motion import AnimateMotion, MPath

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
