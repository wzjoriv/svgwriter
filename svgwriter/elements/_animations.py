"""
User animation presets: ``register_animation`` makes ``element.animate.<name>(...)`` call a function.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final

from .._internal._registry import Registry

if TYPE_CHECKING:
    from ._motion import Motion

__all__ = ["ANIMATIONS", "register_animation", "unregister_animation"]

ANIMATIONS: Final[Registry[Callable[..., Any]]] = Registry("animation")
"""User animation presets by name; ``element.animate.<name>(...)`` calls them."""


def register_animation(name: str, function: Callable[..., Motion | None]) -> None:
    """Make ``element.animate.<name>(*args, **options)`` call ``function(motion, *args, **options)``.

    The function receives the element's :class:`~svgwriter.Motion`, so it can chain the built-in
    presets (``motion.move_by(...)``, ``motion.fade_in(...)``) or add SMIL children to
    ``motion.element`` itself. The call returns the motion, so user presets chain like the built-in
    ones and work with :meth:`Motion.stagger <svgwriter.Motion.stagger>`.

    Parameters
    ----------
    name : str
        A Python identifier, used as the method name.
    function : callable
        ``function(motion, *args, **options)``; its return value is ignored.

    Raises
    ------
    ValueError
        If *name* is not an identifier, is a built-in preset, or is already registered.

    See Also
    --------
    unregister_animation : Remove it again.
    ANIMATIONS : Every registered preset.

    Examples
    --------
    >>> import svgwriter as svg
    >>> def bob(motion, height=8.0, dur=1.0, **timing):
    ...     motion.move_by(0, -height, dur / 2, **timing)
    ...     motion.move_by(0, height, dur / 2, begin=timing.get("begin", 0) + dur / 2)
    >>> svg.register_animation("bob", bob)
    >>> dot = svg.circle(10, 10, 4)
    >>> _ = dot.animate.bob(height=4).fade_out(begin=1)
    >>> [child.tag for child in dot.children]
    ['animateTransform', 'animateTransform', 'animate']
    >>> svg.register_animation("fade_in", bob)
    Traceback (most recent call last):
    ...
    ValueError: 'fade_in' is a built-in animation preset
    >>> svg.unregister_animation("bob")
    """
    from ._motion import Motion

    if not name.isidentifier() or name.startswith("_"):
        raise ValueError(f"animation names are Python identifiers without a leading underscore, not {name!r}")
    if hasattr(Motion, name):
        raise ValueError(f"{name!r} is a built-in animation preset")
    ANIMATIONS.add(name, function)


def unregister_animation(name: str) -> None:
    """Remove a preset added with :func:`register_animation`.

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
    >>> svg.register_animation("nudge", lambda motion, dx=2: motion.move_by(dx, 0))
    >>> svg.unregister_animation("nudge")
    >>> "nudge" in svg.ANIMATIONS
    False
    """
    ANIMATIONS.remove(name)
