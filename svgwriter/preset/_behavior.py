"""
``@svg.preset.behavior``: a function of the element and the time, run by a scene before every frame.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TypeVar, overload

from .._internal._constants import MOTION_HELPERS
from .._internal._presets import ANIMATIONS, BEHAVIORS

__all__ = ["behavior"]

F = TypeVar("F", bound=Callable[..., None])

_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


def _check(name: str, function: Callable[..., object]) -> None:
    """Raise unless *name* is usable and *function* is ``f(element, seconds, *, option=default, ...)``."""
    if not name.isidentifier() or name.startswith("_") or name in MOTION_HELPERS:
        raise ValueError(f"behavior names are Python identifiers, without a leading underscore and other than "
                         f"{', '.join(sorted(MOTION_HELPERS))}; not {name!r}")
    if name in ANIMATIONS:
        raise ValueError(f"{name!r} is an animation preset; behaviors and animations share element.animate, "
                         "so pick another name")
    parameters = list(inspect.signature(function).parameters.values())
    shape = f"def {name}(element: svg.Element, seconds: float, *, option: float = 1.0) -> None"
    if len(parameters) < 2 or any(parameter.kind not in _POSITIONAL for parameter in parameters[:2]):
        raise TypeError(f"behavior {name!r} takes the element and the time in seconds as its first two "
                        f"positional parameters: {shape}")
    for parameter in parameters[2:]:
        keyword = parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is not inspect.Parameter.empty
        if not keyword and parameter.kind is not inspect.Parameter.VAR_KEYWORD:
            raise TypeError(f"behavior {name!r}: option {parameter.name!r} must be keyword-only with a default: "
                            f"{shape}")


@overload
def behavior(function: F, /) -> F: ...


@overload
def behavior(*, name: str | None = None, replace: bool = False) -> Callable[[F], F]: ...


def behavior(function: F | None = None, /, *, name: str | None = None, replace: bool = False) -> F | Callable[[F], F]:
    """Register a function as a behavior: Python motion that a :class:`~svgwriter.Scene` runs before every frame.

    A behavior sets the element's state at an absolute time, so frames can be drawn in any order. Attach it
    with :meth:`Scene.attach <svgwriter.Scene.attach>` (typed with the function's own options) or by name,
    ``element.animate.<name>(...)``, once the element is in a scene's document. Saving the scene as SVG or
    PowerPoint bakes it into SMIL (:meth:`Scene.bake <svgwriter.Scene.bake>`).

    Parameters
    ----------
    function : callable, optional
        ``function(element, seconds, *, option=default, ...) -> None``: the element and the time in seconds
        come first, and every option is keyword-only with a default. Given when used as a bare decorator.
    name : str, optional
        The behavior name. Defaults to None, which takes the function's name.
    replace : bool, optional
        Replace a behavior already registered under the name, a built-in one included. Defaults to False.

    Returns
    -------
    callable
        The function unchanged, or a decorator that registers and returns it.

    Raises
    ------
    TypeError
        If the function's parameters do not have that shape.
    ValueError
        If the name is not an identifier, is an animation preset's, or is taken and `replace` is False; the
        message names the owner.

    See Also
    --------
    svgwriter.preset.animation : SMIL presets, the other half of ``element.animate``.
    svgwriter.Element.home : The element as it was when its first behavior was attached.

    Notes
    -----
    Start from :attr:`element.home <svgwriter.Element.home>` rather than the current state, so each frame
    is computed afresh instead of adding to the last one: ``element.t = element.home.t`` and then a
    relative move.

    Examples
    --------
    >>> import math
    >>> import svgwriter as svg
    >>> @svg.preset.behavior
    ... def sway(element: svg.Element, seconds: float, *, angle: float = 10, period: float = 2) -> None:
    ...     element.t = element.home.t
    ...     element.rotate(angle * math.sin(2 * math.pi * seconds / period))
    >>> class Flag(svg.Scene):
    ...     width, height, duration = 40, 40, 2.0
    ...     def build(self, doc):
    ...         doc.rect(15, 5, 10, 30).animate.sway(angle=20)
    >>> scene = Flag()
    >>> scene.render(0.5)[:4]
    b'\\x89PNG'
    >>> svg.preset.behavior(sway)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: behavior 'sway' is already registered by ...sway; pass replace=True to replace it
    >>> svg.preset.unregister("behavior", "sway")
    """

    def register(item: F) -> F:
        label = name or item.__name__
        _check(label, item)
        BEHAVIORS.add(label, item, replace=replace)
        return item

    return register if function is None else register(function)
