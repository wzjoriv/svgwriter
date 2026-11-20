"""
Shared pieces of the SMIL animation elements: value helpers, private bases and shortcut constructors.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from ..._internal._typing import Self
from ..core import Child, Element
from ._easing import EaseLike, apply_ease

if TYPE_CHECKING:
    from ._elements import Accumulate, Additive, CalcMode, Clock

__all__ = ["FadeShortcut", "SpinShortcut"]


def _clock(value: Clock | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return f"{value:g}s"


def _list(value: Any, separator: str = ";") -> Any:
    if isinstance(value, (list, tuple)):
        return separator.join(str(v) for v in value)
    return value


class _AttributeTarget(Element):
    def __init__(
        self,
        *args: Child,
        attribute_name: str | None = None,
        attribute_type: Literal["CSS", "XML", "auto"] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.update(attribute_name=attribute_name, attribute_type=attribute_type)


class _ValueAnimation(Element):
    def __init__(
        self,
        *args: Child,
        values: Sequence[Any] | str | None = None,
        from_: Any = None,
        to: Any = None,
        by: Any = None,
        calc_mode: CalcMode | None = None,
        key_times: Sequence[float] | str | None = None,
        key_splines: Sequence[tuple[float, float, float, float]] | str | None = None,
        additive: Additive | None = None,
        accumulate: Accumulate | None = None,
        ease: EaseLike | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        if isinstance(key_splines, (list, tuple)):
            key_splines = ";".join(" ".join(f"{n:g}" for n in spline) for spline in key_splines)
        self.update(
            values=_list(values),
            from_=from_,
            to=to,
            by=by,
            calc_mode=calc_mode,
            key_times=_list(key_times),
            key_splines=key_splines,
            additive=additive,
            accumulate=accumulate,
        )
        if ease is not None:
            apply_ease(self, ease)


class FadeShortcut:
    """The ``fade`` shortcut; mixed into :class:`~svgwriter.elements.Animate`."""

    __slots__ = ()

    @classmethod
    def fade(cls, start: float, stop: float, **kwargs: Any) -> Self:
        """Create an opacity animation.

        Parameters
        ----------
        start : float
            Opacity at the beginning.
        stop : float
            Opacity at the end.
        **kwargs
            Further attributes, typically timing such as ``dur``.

        Returns
        -------
        Animate
            An ``<animate>`` of ``opacity`` from *start* to *stop*.

        Examples
        --------
        >>> from svgwriter.elements.animation import Animate
        >>> Animate.fade(0, 1, dur=1).get("to")
        1
        """
        return cls(attribute_name="opacity", from_=start, to=stop, **kwargs)


class SpinShortcut:
    """The ``spin`` shortcut; mixed into :class:`~svgwriter.elements.AnimateTransform`."""

    __slots__ = ()

    @classmethod
    def spin(cls, cx: float = 0, cy: float = 0, **kwargs: Any) -> Self:
        """Create an endlessly repeating full clockwise rotation.

        Parameters
        ----------
        cx, cy : float, optional
            The center of rotation. Defaults to 0.
        **kwargs
            Further attributes, typically ``dur``; ``repeat_count`` defaults to
            infinite.

        Returns
        -------
        AnimateTransform
            A rotation from 0 to 360 degrees about ``(cx, cy)``.

        Examples
        --------
        >>> from svgwriter.elements.animation import AnimateTransform
        >>> AnimateTransform.spin(5, 5, dur=3).get("to")
        '360 5 5'
        """
        from ._elements import TransformType

        kwargs.setdefault("repeat_count", float("inf"))
        return cls(TransformType.ROTATE, from_=f"0 {cx:g} {cy:g}", to=f"360 {cx:g} {cy:g}", **kwargs)
