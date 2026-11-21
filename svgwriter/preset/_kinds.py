"""
Looking presets up across kinds: ``list``, ``get`` and ``unregister``.
"""

from __future__ import annotations

import builtins
from typing import Any

from .._internal._presets import KINDS, PresetRegistry

__all__ = ["get", "list", "registry", "unregister"]


def registry(kind: str) -> PresetRegistry:
    """The registry of *kind*; an unknown kind raises ValueError listing the kinds."""
    try:
        return KINDS[kind]
    except KeyError:
        raise ValueError(f"unknown preset kind {kind!r}; kinds: {', '.join(KINDS)}") from None


def list(kind: str) -> builtins.list[str]:
    """The names of every preset of *kind*: built-in ones first, then the ones registered since.

    Parameters
    ----------
    kind : str
        ``"animation"``, ``"behavior"`` or ``"shape"``.

    Returns
    -------
    list of str
        The names.

    Raises
    ------
    ValueError
        If *kind* is unknown.

    Examples
    --------
    >>> import svgwriter as svg
    >>> "fade_in" in svg.preset.list("animation"), "star" in svg.preset.list("shape")
    (True, True)
    """
    return registry(kind).names()


def get(kind: str, name: str) -> Any:
    """The preset of *kind* registered as *name*: the user's if one replaced it, else the built-in.

    Parameters
    ----------
    kind : str
        ``"animation"``, ``"behavior"`` or ``"shape"``.
    name : str
        The preset name.

    Returns
    -------
    callable
        A shape factory, an animation function ``f(motion, ...)`` for :meth:`Motion.apply
        <svgwriter.Motion.apply>`, or a behavior ``f(element, seconds, ...)`` for :meth:`Scene.attach
        <svgwriter.Scene.attach>`.

    Raises
    ------
    KeyError
        If no preset has that name; the message suggests the closest names.
    ValueError
        If *kind* is unknown.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.preset.get("shape", "star")(0, 0, 10).tag
    'polygon'
    >>> svg.preset.get("shape", "gearr")  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    KeyError: "unknown shape 'gearr'; did you mean 'gear'...?"
    """
    return registry(kind).get(name)


def unregister(kind: str, name: str) -> None:
    """Remove a preset registered with a :mod:`svgwriter.preset` decorator; a replaced built-in comes back.

    Parameters
    ----------
    kind : str
        ``"animation"``, ``"behavior"`` or ``"shape"``.
    name : str
        The registered name.

    Raises
    ------
    KeyError
        If no user preset has that name (built-in presets cannot be removed, only replaced).
    ValueError
        If *kind* is unknown.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.preset.unregister("shape", "star")
    Traceback (most recent call last):
    ...
    KeyError: "shape 'star' is built in; replace it with replace=True instead"
    """
    registry(kind).remove(name)
