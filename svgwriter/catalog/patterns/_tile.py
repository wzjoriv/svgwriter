"""
Pattern tiles: the ``<pattern>`` around a tile's shapes, and the themed ink of those shapes.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypeVar

from ..._internal._roles import with_role
from ...model.color.color import Color
from ...model.elements import Pattern, Rect
from ...model.elements.core import Element
from ._constants import FALLBACK_INK

__all__ = ["ink", "tile"]

E = TypeVar("E", bound=Element)


def ink(shape: E, color: Color | str | None, role: str | None) -> E:
    """Fill *shape* with *color*, or with the theme *role* (black without a theme) when *color* is None."""
    if color is not None:
        shape.fill = color
        return shape
    if role is None:
        shape.fill = FALLBACK_INK
        return shape
    return with_role(shape, role, (), {"fill": FALLBACK_INK})


def tile(width: float, height: float, shapes: Iterable[Element], *, angle: float = 0.0,
         background: Color | str | None = None, **kwargs: Any) -> Pattern:
    """A user-space ``<pattern>`` repeating a *width* by *height* tile of *shapes*, turned by *angle* degrees."""
    kwargs.setdefault("pattern_units", "userSpaceOnUse")
    if angle:
        kwargs.setdefault("pattern_transform", f"rotate({angle:g})")
    backdrop = [Rect(0, 0, width, height, fill=background)] if background is not None else []
    return Pattern(*backdrop, *shapes, x=0, y=0, width=width, height=height, **kwargs)
