"""
Theme roles for builder shapes: the role class plus caller attributes kept ahead of it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TypeVar

from ..attributes.names import PRESENTATION_ATTRIBUTES, svg_name
from ..elements.core import Element
from ..theme.theme import Theme

__all__ = ["with_role"]

E = TypeVar("E", bound=Element)


def with_role(element: E, role: str | None, given: Iterable[str], fallback: Mapping[str, object] | None = None) -> E:
    """Mark *element* with *role*; presentation attributes the caller *given* move into its inline style.

    The theme rule overrides plain attributes, so the caller's choices are kept in ``style`` where they
    still win. *fallback* attributes apply when no theme sheet is present (an element written on its own).
    """
    if role is None:
        return element
    names = {svg_name(key) for key in given} & PRESENTATION_ATTRIBUTES
    style = element.style
    for name in sorted(names):
        if name in element.attributes:
            style[name] = element.attributes.pop(name)
    element.style = style
    for name, value in (fallback or {}).items():
        if name not in style and name not in element.attributes:
            element.attributes[name] = value
    element.add_class(Theme.class_name(role))
    return element
