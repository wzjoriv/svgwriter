"""
SMIL animation elements.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from typing import Any, Literal, TypeAlias

from ...pathdata.builder import PathBuilder
from ...pathdata.data import PathData
from .._behavior import ConditionalAttributes, CoreAttributes, ExternalResourcesAttribute, XLinkAttributes
from ..core import Category, Child, ContentModel, Element
from ._smil import FadeShortcut, SpinShortcut, _AttributeTarget, _clock, _list, _ValueAnimation

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
    "Clock",
    "MPath",
    "Restart",
    "Set",
    "TransformType",
]

Clock: TypeAlias = str | float
RepeatCount: TypeAlias = float | Literal["indefinite"]


class Restart(str, enum.Enum):
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


class AnimationFill(str, enum.Enum):
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


class CalcMode(str, enum.Enum):
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


class Additive(str, enum.Enum):
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


class Accumulate(str, enum.Enum):
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


class TransformType(str, enum.Enum):
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


class AnimationElement(
    XLinkAttributes,
    ConditionalAttributes,
    ExternalResourcesAttribute,
    CoreAttributes,
    category=Category.ANIMATION,
):
    """Timing attributes shared by every animation element.

    Numeric clock values are written in seconds; ``float("inf")`` for
    ``repeat_count`` is written as ``indefinite``.

    Parameters
    ----------
    *args : Element
        Child elements.
    begin, dur, end, min, max : float or str, optional
        Clock values: seconds as a number or any SMIL timing string.
    restart : Restart, optional
        When the animation may restart. Defaults to ``Restart.ALWAYS``, which
        is not written.
    repeat_count : float or "indefinite", optional
        Number of repeats.
    repeat_dur : float or str, optional
        Total duration of the repeats.
    fill : AnimationFill, optional
        State after the animation ends.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Animate : Interpolate an attribute.
    Set : Assign a value.

    Examples
    --------
    >>> str(Set("fill", "red", begin=1, dur=2))
    '<set attributeName="fill" begin="1s" dur="2s" to="red"/>'
    """

    def __init__(
        self,
        *args: Child,
        begin: Clock | None = None,
        dur: Clock | None = None,
        end: Clock | None = None,
        min: Clock | None = None,
        max: Clock | None = None,
        restart: Restart = Restart.ALWAYS,
        repeat_count: RepeatCount | None = None,
        repeat_dur: Clock | None = None,
        fill: AnimationFill | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            begin=_clock(begin),
            dur=_clock(dur),
            end=_clock(end),
            min=_clock(min),
            max=_clock(max),
            restart=None if restart is Restart.ALWAYS else restart,
            repeat_count=repeat_count,
            repeat_dur=_clock(repeat_dur),
            fill=fill,
        )


class Animate(FadeShortcut, AnimationElement, _ValueAnimation, _AttributeTarget, tag="animate"):
    """``<animate>``: interpolate one attribute over time.

    Parameters
    ----------
    attribute_name : str, optional
        The attribute to animate.
    attribute_type : {"CSS", "XML", "auto"}, optional
        Namespace of the attribute.
    values : sequence or str, optional
        The values to pass through.
    from_ : object, optional
        Start value (written ``from``).
    to : object, optional
        End value.
    by : object, optional
        Relative change.
    calc_mode : CalcMode, optional
        Interpolation mode.
    key_times : sequence of float or str, optional
        Times of each value, 0 to 1.
    key_splines : sequence of 4-tuples or str, optional
        Bezier control points for spline mode.
    additive : Additive, optional
        Combination with the underlying value.
    accumulate : Accumulate, optional
        Whether repeats accumulate.
    **kwargs
        Timing (``begin``, ``dur``, ``repeat_count`` and so on, see
        :class:`AnimationElement`), core and other SVG attributes.

    See Also
    --------
    Set : Assign a value instead of interpolating.
    AnimateTransform : Animate the ``transform`` attribute.

    Examples
    --------
    >>> str(Animate.fade(1, 0, dur=2))
    '<animate attributeName="opacity" from="1" to="0" dur="2s"/>'
    """


class Set(AnimationElement, _AttributeTarget, tag="set"):
    """``<set>``: assign a value for a duration.

    Parameters
    ----------
    attribute_name : str, optional
        The attribute to set.
    to : object, optional
        The value to assign.
    **kwargs
        Timing (see :class:`AnimationElement`), core and other SVG attributes.

    See Also
    --------
    Animate : Interpolate instead of assigning.

    Examples
    --------
    >>> str(Set("visibility", "hidden", begin=2))
    '<set attributeName="visibility" begin="2s" to="hidden"/>'
    """

    def __init__(self, attribute_name: str | None = None, to: Any = None, **kwargs: Any) -> None:
        super().__init__(attribute_name=attribute_name, **kwargs)
        self.update(to=to)


class AnimateColor(AnimationElement, _ValueAnimation, _AttributeTarget, tag="animateColor"):
    """``<animateColor>``: color interpolation (deprecated in later SVG).

    Takes the same parameters as :class:`Animate`.

    See Also
    --------
    Animate : Preferred, as it also interpolates colors.

    Examples
    --------
    >>> str(AnimateColor(attribute_name="fill", from_="red", to="blue"))
    '<animateColor attributeName="fill" from="red" to="blue"/>'
    """


class AnimateTransform(SpinShortcut, AnimationElement, _ValueAnimation, _AttributeTarget, tag="animateTransform"):
    """``<animateTransform>``: animate the ``transform`` attribute.

    Parameters
    ----------
    type : TransformType, optional
        Kind of transform. Defaults to ``TransformType.TRANSLATE``.
    **kwargs
        Everything :class:`Animate` takes; ``attribute_name`` defaults to
        ``"transform"``.

    See Also
    --------
    Animate : Animate any other attribute.

    Examples
    --------
    >>> AnimateTransform(TransformType.SCALE, from_=1, to=2, dur=1).get("type")
    <TransformType.SCALE: 'scale'>
    """

    def __init__(self, type: TransformType = TransformType.TRANSLATE, **kwargs: Any) -> None:
        kwargs.setdefault("attribute_name", "transform")
        super().__init__(**kwargs)
        self.update(type=type)


class MPath(XLinkAttributes, ExternalResourcesAttribute, CoreAttributes, tag="mpath", category=Category.ANIMATION):
    """``<mpath>``: the motion path of ``animateMotion`` by reference.

    Parameters
    ----------
    href : str or Element, optional
        The path element, or its IRI.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    AnimateMotion : The element that contains it.

    Examples
    --------
    >>> import svgwriter as svg
    >>> p = svg.Path("M0 0L10 10", id="track")
    >>> 'href="#track"' in str(MPath(p))
    True
    """

    def __init__(self, href: str | Element | None = None, **kwargs: Any) -> None:
        super().__init__(href=href, **kwargs)


class AnimateMotion(AnimationElement, _ValueAnimation, tag="animateMotion", content=ContentModel.ELEMENTS):
    """``<animateMotion>``: move an element along a path.

    Parameters
    ----------
    *children : MPath
        An optional ``mpath`` naming the path by reference.
    path : PathData or PathBuilder or str, optional
        The motion path.
    key_points : sequence of float or str, optional
        Progress along the path at each ``key_times`` entry.
    rotate : float or {"auto", "auto-reverse"}, optional
        Orientation along the path.
    origin : str, optional
        The motion origin.
    **kwargs
        Timing (see :class:`AnimationElement`), values attributes, core and
        other SVG attributes.

    See Also
    --------
    MPath : Reference a path instead of inlining it.

    Examples
    --------
    >>> str(AnimateMotion(path="M0 0L10 10", dur=2, rotate="auto"))
    '<animateMotion dur="2s" path="M0 0 L10 10" rotate="auto"/>'
    """

    def __init__(
        self,
        *children: Child,
        path: PathData | PathBuilder | str | None = None,
        key_points: Sequence[float] | str | None = None,
        rotate: float | Literal["auto", "auto-reverse"] | None = None,
        origin: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*children, **kwargs)
        if isinstance(path, PathBuilder):
            path = path.build()
        elif isinstance(path, str):
            path = PathData(path)
        self.update(path=path, key_points=_list(key_points), rotate=rotate, origin=origin)
