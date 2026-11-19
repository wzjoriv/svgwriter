"""
``Composable``: ``a + b`` builds a group.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Element
    from .structure import Group

__all__ = ["Composable"]


class Composable:
    """Mixin giving every element ``+`` and reflected ``+``.

    The operands are moved into the new group, not copied.

    Examples
    --------
    >>> import svgwriter as svg
    >>> pair = svg.circle(0, 0, 1) + svg.rect(0, 0, 1, 1)
    >>> pair.tag, len(pair)
    ('g', 2)
    """

    __slots__ = ()

    def __add__(self: Element, other: Element | Iterable[Element]) -> Group:
        """``a + b``: a new ``<g>`` holding both; operands already in a tree are copied, never moved."""
        from .container import flatten
        from .structure import Group

        try:
            items = flatten(other)
        except TypeError:
            return NotImplemented
        return Group(*(_free(item) for item in (self, *items)))

    def __iadd__(self: Element, other: Element | Iterable[Element]) -> Group:
        """``a += b``: a ``<g>`` holding *a* and *b* takes *a*'s place in its parent."""
        from ._geometry import replace_in_parent
        from .container import flatten
        from .structure import Group

        try:
            items = flatten(other)
        except TypeError:
            return NotImplemented
        group = Group()
        replace_in_parent(self, group)
        group.extend([self, *(_free(item) for item in items)])
        return group

    def __radd__(self: Element, other: Iterable[Element]) -> Group:
        """``[a, b] + c``: a new ``<g>`` holding all three."""
        from .container import flatten
        from .structure import Group

        try:
            items = flatten(other)
        except TypeError:
            return NotImplemented
        return Group(*(_free(item) for item in (*items, self)))


def _free(element: Element) -> Element:
    """*element* itself when detached, else a copy, so operators never take elements out of a tree."""
    return element.clone() if element.parent is not None else element
