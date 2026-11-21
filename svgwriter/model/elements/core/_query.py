"""
Tree queries shared by every element: length, iteration, find, ids and the root.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, TypeVar, overload

if TYPE_CHECKING:
    from ._element import Element

E = TypeVar("E", bound="Element")


class Queryable:
    """Read-only tree navigation; mixed into :class:`~svgwriter.model.elements.Element`."""

    __slots__ = ()

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterator[Element]:
        from ._element import Element

        return (c for c in self.children if isinstance(c, Element))

    def __bool__(self) -> bool:
        return True

    def iter(self, tag: str | None = None, *, max_depth: float = float("inf")) -> Iterator[Element]:
        """Depth-first walk over this element and its descendants.

        Parameters
        ----------
        tag : str, optional
            Yield only elements with this tag. Defaults to None (all).
        max_depth : float, optional
            Deepest level to descend to; ``0`` is this element only.
            Defaults to infinity.

        Yields
        ------
        Element
            Elements in document order, starting with this one.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1), svg.rect(0, 0, 1, 1))
        >>> [e.tag for e in g.iter()]
        ['g', 'circle', 'rect']
        """
        from ._element import Element

        stack: list[tuple[Element, int]] = [(self, 0)]
        while stack:
            element, depth = stack.pop()
            if tag is None or element.tag == tag:
                yield element
            if depth < max_depth:
                stack.extend(
                    (child, depth + 1) for child in reversed(element.children) if isinstance(child, Element)
                )

    @overload
    def find(self, match: type[E]) -> E | None: ...
    @overload
    def find(self, match: str) -> Element | None: ...
    def find(self, match: type[Element] | str) -> Element | None:
        """First descendant (or self) matching a tag or class.

        Parameters
        ----------
        match : str or type
            A tag name or an element class.

        Returns
        -------
        Element or None
            The first match in document order, or None.

        See Also
        --------
        find_all : Every match.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1))
        >>> g.find("circle").tag, g.find("rect")
        ('circle', None)
        """
        return next(iter(self.find_all(match)), None)

    @overload
    def find_all(self, match: type[E]) -> list[E]: ...
    @overload
    def find_all(self, match: str) -> list[Element]: ...
    def find_all(self, match: type[Element] | str) -> list[Element]:
        """Every descendant (and self) matching a tag or class.

        Parameters
        ----------
        match : str or type
            A tag name or an element class.

        Returns
        -------
        list of Element
            The matches in document order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1), svg.circle(1, 1, 1))
        >>> len(g.find_all("circle"))
        2
        """
        if isinstance(match, str):
            return list(self.iter(match))
        return [e for e in self.iter() if isinstance(e, match)]

    def get_element_by_id(self, element_id: str) -> Element | None:
        """Find the element with the given id in this subtree.

        Parameters
        ----------
        element_id : str
            The id to look for.

        Returns
        -------
        Element or None
            The matching element, or None.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1, id="dot"))
        >>> g.get_element_by_id("dot").tag
        'circle'
        """
        index = self.__dict__.get("_id_index")
        found = index.get(element_id) if index is not None else None
        if found is not None and found.get("id") == element_id and _within(found, self):
            return found
        index = {}
        for element in self.iter():
            key = element.get("id")
            if key is not None:
                index.setdefault(str(key), element)
        self.__dict__["_id_index"] = index
        return index.get(element_id)

    def root(self) -> Element:
        """Return the topmost ancestor, or this element if it has no parent.

        Returns
        -------
        Element
            The root of the tree this element belongs to.

        Examples
        --------
        >>> import svgwriter as svg
        >>> c = svg.circle(0, 0, 1)
        >>> g = svg.group(c)
        >>> c.root() is g
        True
        """
        node = self
        while node.parent is not None:
            node = node.parent
        return node


def _within(element: Element, ancestor: Element) -> bool:
    """Whether *element* is *ancestor* or lies below it."""
    node: Element | None = element
    while node is not None:
        if node is ancestor:
            return True
        node = node.parent
    return False


