"""
Animation presets of your own: ``@svg.animation`` makes a typed function ``element.animate.<name>``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Final, TypeVar, overload

from .._internal._registry import Registry

if TYPE_CHECKING:
    from ._motion import Motion

__all__ = ["ANIMATIONS", "animation", "unregister_animation"]

AnimationFunction = Callable[..., "Motion | None"]
F = TypeVar("F", bound=AnimationFunction)

ANIMATIONS: Final[Registry[AnimationFunction]] = Registry("animation")
"""User animation presets by name; ``element.animate.<name>(...)`` calls them."""

_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


def _check(name: str, function: AnimationFunction) -> None:
    """Raise unless *function* is ``f(motion, *, option=default, ...)`` and *name* is free."""
    from ._motion import Motion

    if not name.isidentifier() or name.startswith("_"):
        raise ValueError(f"animation names are Python identifiers without a leading underscore, not {name!r}")
    if hasattr(Motion, name):
        raise ValueError(f"{name!r} is a built-in animation preset")
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
def animation(*, name: str | None = None) -> Callable[[F], F]: ...


def animation(function: F | None = None, /, *, name: str | None = None) -> F | Callable[[F], F]:
    """Register a function as an animation preset, so ``element.animate.<name>(...)`` calls it.

    The function stays an ordinary typed function: :meth:`Motion.apply <svgwriter.Motion.apply>` calls it
    with full completion and type checking, and the name works anywhere presets are looked up by name
    (``element.animate.bob(...)``, :meth:`Motion.stagger <svgwriter.Motion.stagger>`).

    Parameters
    ----------
    function : callable, optional
        ``function(motion, *, option=default, ...) -> Motion``: the first positional parameter is the
        element's :class:`~svgwriter.Motion`, every option is keyword-only with a default, and it returns
        the motion for chaining (returning None is accepted). Given when used as a bare decorator.
    name : str, optional
        The preset name. Defaults to None, which takes the function's name.

    Returns
    -------
    callable
        The function unchanged, or a decorator that registers and returns it.

    Raises
    ------
    TypeError
        If the function's parameters do not have that shape.
    ValueError
        If the name is not an identifier, is a built-in preset, or is already registered.

    See Also
    --------
    unregister_animation : Remove it again.
    ANIMATIONS : Every registered preset.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.animation
    ... def bob(motion: svg.Motion, *, height: float = 8, dur: float = 1, begin: float = 0) -> svg.Motion:
    ...     return motion.move_by(0, -height, dur / 2, begin=begin).move_by(0, height, dur / 2, begin=begin + dur / 2)
    >>> dot = svg.circle(10, 10, 4)
    >>> _ = dot.animate.apply(bob, height=4).fade_out(begin=1)
    >>> _ = dot.animate.bob(begin=2)
    >>> [child.tag for child in dot.children]
    ['animateTransform', 'animateTransform', 'animate', 'animateTransform', 'animateTransform']
    >>> @svg.animation(name="lift")
    ... def lift(motion, height=8):
    ...     return motion.move_by(0, -height)
    Traceback (most recent call last):
    ...
    TypeError: animation 'lift': option 'height' must be keyword-only with a default: ...
    >>> svg.unregister_animation("bob")
    """

    def register(item: F) -> F:
        label = name or item.__name__
        _check(label, item)
        ANIMATIONS.add(label, item)
        return item

    return register if function is None else register(function)


def unregister_animation(name: str) -> None:
    """Remove a preset registered with :func:`animation`.

    Parameters
    ----------
    name : str
        The registered name.

    Raises
    ------
    KeyError
        If no user preset has that name.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.animation
    ... def nudge(motion, *, dx=2.0):
    ...     return motion.move_by(dx, 0)
    >>> svg.unregister_animation("nudge")
    >>> "nudge" in svg.ANIMATIONS
    False
    """
    ANIMATIONS.remove(name)

