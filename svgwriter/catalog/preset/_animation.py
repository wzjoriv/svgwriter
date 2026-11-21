"""
``@svg.preset.animation``: a typed function becomes ``element.animate.<name>``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, overload

from ..._internal._constants import MOTION_HELPERS
from ..._internal._presets import ANIMATIONS, BEHAVIORS

if TYPE_CHECKING:
    from ...model.elements import Motion

__all__ = ["animation"]

F = TypeVar("F", bound=Callable[..., "Motion | None"])

_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


def _check(name: str, function: Callable[..., object]) -> None:
    """Raise unless *name* is usable and *function* is ``f(motion, *, option=default, ...)``."""
    if not name.isidentifier() or name.startswith("_") or name in MOTION_HELPERS:
        raise ValueError(f"animation names are Python identifiers, without a leading underscore and other than "
                         f"{', '.join(sorted(MOTION_HELPERS))}; not {name!r}")
    if name in BEHAVIORS:
        raise ValueError(f"{name!r} is a behavior; animations and behaviors share element.animate, "
                         "so pick another name")
    parameters = list(inspect.signature(function).parameters.values())
    shape = f"def {name}(motion: svg.Motion, *, option: float = 1.0) -> svg.Motion"
    if not parameters or parameters[0].kind not in _POSITIONAL:
        raise TypeError(f"animation {name!r} takes the Motion as its first positional parameter: {shape}")
    for parameter in parameters[1:]:
        keyword = parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is not inspect.Parameter.empty
        if not keyword and parameter.kind is not inspect.Parameter.VAR_KEYWORD:
            raise TypeError(f"animation {name!r}: option {parameter.name!r} must be keyword-only with a default: "
                            f"{shape}")


@overload
def animation(function: F, /) -> F: ...


@overload
def animation(*, name: str | None = None, replace: bool = False) -> Callable[[F], F]: ...


def animation(function: F | None = None, /, *, name: str | None = None, replace: bool = False) -> F | Callable[[F], F]:
    """Register a function as an animation preset, so ``element.animate.<name>(...)`` calls it.

    The function stays an ordinary typed function: :meth:`Motion.apply <svgwriter.Motion.apply>` calls it with
    full completion and type checking, and the name works wherever presets are looked up by name
    (``element.animate.bob(...)``, :meth:`Motion.stagger <svgwriter.Motion.stagger>`).

    Parameters
    ----------
    function : callable, optional
        ``function(motion, *, option=default, ...) -> Motion``: the first positional parameter is the element's
        :class:`~svgwriter.Motion`, every option is keyword-only with a default, and it returns the motion for
        chaining (returning None is accepted). Given when used as a bare decorator.
    name : str, optional
        The preset name. Defaults to None, which takes the function's name.
    replace : bool, optional
        Replace a preset already registered under the name, a built-in one included. Defaults to False.

    Returns
    -------
    callable
        The function unchanged, or a decorator that registers and returns it.

    Raises
    ------
    TypeError
        If the function's parameters do not have that shape.
    ValueError
        If the name is not an identifier, or is taken and `replace` is False; the message names the owner.

    See Also
    --------
    svgwriter.catalog.preset.unregister : Remove it again (``unregister("animation", name)``).
    svgwriter.catalog.preset.list : Every animation preset (``list("animation")``).

    Notes
    -----
    A replaced built-in stays reachable as a class attribute, so a replacement can wrap it:
    ``svg.Motion.spin(motion, ...)``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.animation
    ... def bob(motion: svg.Motion, *, height: float = 8, dur: float = 1, begin: float = 0) -> svg.Motion:
    ...     return motion.move_by(0, -height, dur / 2, begin=begin).move_by(0, height, dur / 2, begin=begin + dur / 2)
    >>> dot = svg.circle(10, 10, 4)
    >>> _ = dot.animate.apply(bob, height=4).fade_out(begin=1)
    >>> _ = dot.animate.bob(begin=2)
    >>> [child.tag for child in dot.children]
    ['animateTransform', 'animateTransform', 'animate', 'animateTransform', 'animateTransform']
    >>> svg.preset.animation(bob)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: animation 'bob' is already registered by ...bob; pass replace=True to replace it
    >>> svg.preset.unregister("animation", "bob")
    """

    def register(item: F) -> F:
        label = name or item.__name__
        _check(label, item)
        ANIMATIONS.add(label, item, replace=replace)
        return item

    return register if function is None else register(function)
