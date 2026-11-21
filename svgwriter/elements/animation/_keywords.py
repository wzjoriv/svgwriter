"""
SMIL animation keywords: restart, fill, calculation, additive, accumulate and transform types.
"""

from __future__ import annotations

from ..._internal._enums import Keyword

__all__ = [
    "Accumulate",
    "Additive",
    "AnimationFill",
    "CalcMode",
    "Restart",
    "TransformType",
]


class Restart(Keyword):
    """The ``restart`` attribute: when an animation may begin again.

    See Also
    --------
    AnimationElement : Takes ``restart`` as an argument.

    Examples
    --------
    >>> Restart.NEVER.value
    'never'
    """

    ALWAYS = "always"
    WHEN_NOT_ACTIVE = "whenNotActive"
    NEVER = "never"


class AnimationFill(Keyword):
    """The animation ``fill`` attribute: the state after the active duration (not paint).

    See Also
    --------
    AnimationElement : Takes ``fill`` as an argument.

    Examples
    --------
    >>> AnimationFill.FREEZE.value
    'freeze'
    """

    FREEZE = "freeze"
    REMOVE = "remove"


class CalcMode(Keyword):
    """The ``calcMode`` attribute: how values are interpolated.

    See Also
    --------
    Animate : Takes ``calc_mode`` as an argument.

    Examples
    --------
    >>> CalcMode.SPLINE.value
    'spline'
    """

    DISCRETE = "discrete"
    LINEAR = "linear"
    PACED = "paced"
    SPLINE = "spline"


class Additive(Keyword):
    """The ``additive`` attribute: replace the underlying value or add to it.

    See Also
    --------
    Accumulate : Repeat-iteration counterpart.

    Examples
    --------
    >>> Additive.SUM.value
    'sum'
    """

    REPLACE = "replace"
    SUM = "sum"


class Accumulate(Keyword):
    """The ``accumulate`` attribute: whether repeats build on the previous end value.

    See Also
    --------
    Additive : Controls combination with the underlying value.

    Examples
    --------
    >>> Accumulate.NONE.value
    'none'
    """

    NONE = "none"
    SUM = "sum"


class TransformType(Keyword):
    """The ``type`` of an ``animateTransform``.

    See Also
    --------
    AnimateTransform : Takes the type as its first argument.

    Examples
    --------
    >>> TransformType.SKEW_X.value
    'skewX'
    """

    TRANSLATE = "translate"
    SCALE = "scale"
    ROTATE = "rotate"
    SKEW_X = "skewX"
    SKEW_Y = "skewY"
