"""
``@svg.preset.pattern``, ``filter``, ``gradient`` and ``marker``: factories of reusable definitions.

Each decorated function joins its catalogue (``svg.patterns``, ``svg.filters``, ``svg.gradients``,
``svg.markers``) and is checked to return the right element when called.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, overload

from .._internal._presets import FILTERS, GRADIENTS, MARKERS, PATTERNS, PresetRegistry
from .._internal._typing import P

if TYPE_CHECKING:
    from ..model.elements.core import Element

__all__ = ["filter", "gradient", "marker", "pattern"]

E = TypeVar("E", bound="Element")
Decorator = Callable[[Callable[P, E]], Callable[P, E]]


def _types(kind: str) -> tuple[type, ...]:
    from ..model.elements import Filter, LinearGradient, Marker, Pattern, RadialGradient

    return {"pattern": (Pattern,), "filter": (Filter,), "gradient": (LinearGradient, RadialGradient, Pattern),
            "marker": (Marker,)}[kind]


def _register(registry: PresetRegistry, function: Callable[P, E] | None, name: str | None,
              replace: bool) -> Callable[P, E] | Decorator[P, E]:
    """Register *function* (or return a decorator that does) behind a wrapper checking its return type."""

    def decorate(func: Callable[P, E]) -> Callable[P, E]:
        label = name or func.__name__
        expected = _types(registry.kind)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> E:
            result = func(*args, **kwargs)
            if not isinstance(result, expected):
                names = " or ".join(kind.__name__ for kind in expected)
                raise TypeError(f"{registry.kind} {label!r} returned {type(result).__name__}, not {names}")
            return result

        registry.add(label, wrapper, replace=replace)
        return wrapper

    return decorate if function is None else decorate(function)


@overload
def pattern(function: Callable[P, E], /, *, name: str | None = None, replace: bool = False) -> Callable[P, E]: ...


@overload
def pattern(*, name: str | None = None, replace: bool = False) -> Decorator[P, E]: ...


def pattern(function: Callable[P, E] | None = None, /, *, name: str | None = None,
            replace: bool = False) -> Callable[P, E] | Decorator[P, E]:
    """Register a function returning a :class:`~svgwriter.Pattern` as a pattern preset.

    The pattern then answers as ``svg.patterns.<name>(...)`` and by name through
    :func:`svgwriter.preset.get`. A pattern is a paint: ``fill=pattern`` puts it into ``<defs>``.

    Parameters
    ----------
    function : callable, optional
        The function, returning a pattern. Given when used as a bare decorator.
    name : str, optional
        The preset name. Defaults to None, which takes the function's name.
    replace : bool, optional
        Replace a pattern already registered under the name, a built-in one included. Defaults to False.

    Returns
    -------
    callable
        The checking wrapper, or a decorator that registers the function and returns that wrapper.

    Raises
    ------
    ValueError
        If the name is taken and `replace` is False; the message names the owner.
    TypeError
        When the decorated function is called and does not return a pattern.

    See Also
    --------
    svgwriter.patterns : The built-in patterns.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.pattern
    ... def bricks(size: float = 8, color: str = "firebrick") -> svg.Pattern:
    ...     return svg.Pattern(svg.rect(0, 0, size, size / 2, fill=color), width=size, height=size,
    ...                        pattern_units="userSpaceOnUse")
    >>> svg.patterns.bricks(4).tag
    'pattern'
    >>> svg.preset.unregister("pattern", "bricks")
    """
    return _register(PATTERNS, function, name, replace)


@overload
def filter(function: Callable[P, E], /, *, name: str | None = None, replace: bool = False) -> Callable[P, E]: ...  # noqa: A001


@overload
def filter(*, name: str | None = None, replace: bool = False) -> Decorator[P, E]: ...  # noqa: A001


def filter(function: Callable[P, E] | None = None, /, *, name: str | None = None,  # noqa: A001
           replace: bool = False) -> Callable[P, E] | Decorator[P, E]:
    """Register a function returning a :class:`~svgwriter.Filter` as a filter preset.

    The filter then answers as ``svg.filters.<name>(...)``; ``element.filter = ...`` puts it into ``<defs>``.

    Parameters
    ----------
    function : callable, optional
        The function, returning a filter. Given when used as a bare decorator.
    name : str, optional
        The preset name. Defaults to None, which takes the function's name.
    replace : bool, optional
        Replace a filter already registered under the name, a built-in one included. Defaults to False.

    Returns
    -------
    callable
        The checking wrapper, or a decorator that registers the function and returns that wrapper.

    Raises
    ------
    ValueError
        If the name is taken and `replace` is False; the message names the owner.
    TypeError
        When the decorated function is called and does not return a filter.

    See Also
    --------
    svgwriter.filters : The built-in filters.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.filter
    ... def soften(amount: float = 1.5) -> svg.Filter:
    ...     return svg.Filter(svg.FeGaussianBlur(amount))
    >>> svg.filters.soften().children[0].tag
    'feGaussianBlur'
    >>> svg.preset.unregister("filter", "soften")
    """
    return _register(FILTERS, function, name, replace)


@overload
def gradient(function: Callable[P, E], /, *, name: str | None = None, replace: bool = False) -> Callable[P, E]: ...


@overload
def gradient(*, name: str | None = None, replace: bool = False) -> Decorator[P, E]: ...


def gradient(function: Callable[P, E] | None = None, /, *, name: str | None = None,
             replace: bool = False) -> Callable[P, E] | Decorator[P, E]:
    """Register a function returning a gradient (or a pattern of blended gradients) as a gradient preset.

    The gradient then answers as ``svg.gradients.<name>(...)``; ``fill=gradient`` puts it into ``<defs>``.

    Parameters
    ----------
    function : callable, optional
        The function, returning a :class:`~svgwriter.LinearGradient`, :class:`~svgwriter.RadialGradient`
        or :class:`~svgwriter.Pattern`. Given when used as a bare decorator.
    name : str, optional
        The preset name. Defaults to None, which takes the function's name.
    replace : bool, optional
        Replace a gradient already registered under the name, a built-in one included. Defaults to False.

    Returns
    -------
    callable
        The checking wrapper, or a decorator that registers the function and returns that wrapper.

    Raises
    ------
    ValueError
        If the name is taken and `replace` is False; the message names the owner.
    TypeError
        When the decorated function is called and does not return a paint server.

    See Also
    --------
    svgwriter.gradients : The built-in gradients.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.gradient
    ... def dusk() -> svg.LinearGradient:
    ...     return svg.LinearGradient.vertical("navy", "orchid")
    >>> len(svg.gradients.dusk().children)
    2
    >>> svg.preset.unregister("gradient", "dusk")
    """
    return _register(GRADIENTS, function, name, replace)


@overload
def marker(function: Callable[P, E], /, *, name: str | None = None, replace: bool = False) -> Callable[P, E]: ...


@overload
def marker(*, name: str | None = None, replace: bool = False) -> Decorator[P, E]: ...


def marker(function: Callable[P, E] | None = None, /, *, name: str | None = None,
           replace: bool = False) -> Callable[P, E] | Decorator[P, E]:
    """Register a function returning a :class:`~svgwriter.Marker` as a marker preset.

    The marker then answers as ``svg.markers.<name>(...)``; ``marker_end=marker`` puts it into ``<defs>``.

    Parameters
    ----------
    function : callable, optional
        The function, returning a marker. Given when used as a bare decorator.
    name : str, optional
        The preset name. Defaults to None, which takes the function's name.
    replace : bool, optional
        Replace a marker already registered under the name, a built-in one included. Defaults to False.

    Returns
    -------
    callable
        The checking wrapper, or a decorator that registers the function and returns that wrapper.

    Raises
    ------
    ValueError
        If the name is taken and `replace` is False; the message names the owner.
    TypeError
        When the decorated function is called and does not return a marker.

    See Also
    --------
    svgwriter.markers : The built-in markers.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.marker
    ... def tick(size: float = 4) -> svg.Marker:
    ...     return svg.Marker(svg.rect(0, 0, 1, size), ref_x=0.5, ref_y=size / 2, orient="auto")
    >>> svg.markers.tick().get("orient")
    'auto'
    >>> svg.preset.unregister("marker", "tick")
    """
    return _register(MARKERS, function, name, replace)
