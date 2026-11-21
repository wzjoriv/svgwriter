"""
Shared filter parts: the enlarged filter region and a flood in a color or a theme role.
"""

from __future__ import annotations

from typing import Any

from .._internal._roles import with_role
from .._internal._typing import Opacity
from ..color.color import Color
from ..elements import FeFlood, Filter
from ..elements.core import Element
from ._constants import FILTER_EXTENT, FILTER_MARGIN, SRGB

__all__ = ["flood", "region"]


def region(*primitives: Element, margin: str = FILTER_MARGIN, extent: str = FILTER_EXTENT, **kwargs: Any) -> Filter:
    """A filter of *primitives* whose region reaches *margin* beyond the element, computed in sRGB."""
    kwargs.setdefault("x", margin)
    kwargs.setdefault("y", margin)
    kwargs.setdefault("width", extent)
    kwargs.setdefault("height", extent)
    kwargs.setdefault("color_interpolation_filters", SRGB)
    return Filter(*primitives, **kwargs)


def flood(color: Color | str | None, opacity: Opacity, role: str | None, fallback: str) -> FeFlood:
    """A flood of *color*, or of the theme *role*'s ``flood-color`` (*fallback* without a theme) when it is None."""
    if color is not None or role is None:
        return FeFlood(color if color is not None else fallback, opacity)
    return with_role(FeFlood(None, opacity), role, (), {"flood-color": fallback})
