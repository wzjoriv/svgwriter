"""
``@svg.preset.shape``: a function returning an element becomes a named shape preset.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, overload

from .._internal._presets import SHAPES
from .._internal._roles import with_role
from .._internal._typing import P

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["shape"]

E = TypeVar("E", bound="Element")


@overload
def shape(function: Callable[P, E], /, *, name: str | None = None, role: str | None = "shape",
          replace: bool = False) -> Callable[P, E]: ...


@overload
def shape(*, name: str | None = None, role: str | None = "shape",
          replace: bool = False) -> Callable[[Callable[P, E]], Callable[P, E]]: ...


def shape(function: Callable[P, E] | None = None, /, *, name: str | None = None, role: str | None = "shape",
          replace: bool = False) -> Callable[P, E] | Callable[[Callable[P, E]], Callable[P, E]]:
    """Register a function returning an element as a shape preset.

    The wrapper checks the return type, so plugins fail loudly, and marks the element with a theme *role*;
    presentation keywords the caller passes move into the inline style so they keep priority over the role.
    Shape presets are listed by ``svgwriter shapes`` and drawn by ``svgwriter draw``.

    Parameters
    ----------
    function : callable, optional
        The function, returning an element. Given when used as a bare decorator.
    name : str, optional
        The shape name. Defaults to None, which takes the function's name.
    role : str or None, optional
        Theme role of the shapes built (see :class:`~svgwriter.Theme`). Defaults to ``"shape"`` (filled with
        the palette's primary color); None leaves them unthemed.
    replace : bool, optional
        Replace a shape already registered under the name, a built-in one included. Defaults to False.

    Returns
    -------
    callable
        The checking wrapper, or a decorator that registers the function and returns that wrapper.

    Raises
    ------
    ValueError
        If the name is taken and `replace` is False; the message names the owner.
    TypeError
        When the decorated function is called and does not return an element.

    See Also
    --------
    svgwriter.preset.get : Look a shape up by name (``get("shape", name)``).
    svgwriter.preset.list : Every shape preset (``list("shape")``).

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.shape
    ... def disc(cx, cy, r, **kwargs):
    ...     return svg.Circle(cx, cy, r, **kwargs)
    >>> str(disc(0, 0, 2, stroke="red"))
    '<circle cx="0" cy="0" r="2" style="stroke:red" class="role-shape"/>'
    >>> svg.preset.shape(name="star")(disc)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: shape 'star' is already registered by svgwriter.builder._shapes.star (built in); pass replace=True ...
    >>> svg.preset.unregister("shape", "disc")
    """

    def decorate(func: Callable[P, E]) -> Callable[P, E]:
        from ..elements.core import Element

        label = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> E:
            result = func(*args, **kwargs)
            if not isinstance(result, Element):
                raise TypeError(f"shape {label!r} returned {type(result).__name__}")
            return with_role(result, role, kwargs)

        SHAPES.add(label, wrapper, replace=replace)
        return wrapper

    return decorate if function is None else decorate(function)
