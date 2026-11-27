"""
Child editing for ``Element``: append, insert, remove and text content.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Iterator, Mapping
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from ._categories import ContentModel

if TYPE_CHECKING:
    from ._element import C, Child, Element

__all__ = ["TreeEditing", "references_of"]


def references_of(element: Element) -> Iterator[Element]:
    """The elements *element*'s own attributes point at, inline ``style`` properties included."""
    for value in element.attributes.values():
        for item in value.values() if isinstance(value, Mapping) else (value,):
            target = getattr(item, "element", None)
            if target is not None:
                yield target


def _foreign_definition(target: Element, root: Element) -> bool:
    """Whether *target* is a top-level definition of another document that this one has no copy of."""
    owner = target.root()
    if owner is root or owner.tag != "svg" or target.parent is None or target.parent.tag != "defs":
        return False
    return target.id is None or root.get_element_by_id(target.id) is None  # type: ignore[attr-defined]


def _point_at_copy(element: Element, target: Element, root: Element) -> None:
    """Point *element* at this document's copy of *target*, a definition owned by another document."""
    copies = root.__dict__.setdefault("_foreign_definitions", {})
    copy = copies.get(id(target))
    if copy is None:
        copy = copies[id(target)] = deepcopy(target)
        root.defs().append(copy)  # type: ignore[attr-defined]
    for name, value in list(element.attributes.items()):
        if isinstance(value, Mapping):
            element.attributes[name] = type(value)({key: _swap(item, target, copy) for key, item in value.items()})
        else:
            element.attributes[name] = _swap(value, target, copy)


def _swap(value: Any, target: Element, copy: Element) -> Any:
    """*value* pointing at *copy* instead of *target*; other values unchanged."""
    if getattr(value, "element", None) is target and dataclasses.is_dataclass(value):
        return dataclasses.replace(value, element=copy)
    return value


class TreeEditing:
    """Adding, inserting and removing children; mixed into :class:`~svgwriter.model.elements.Element`."""

    __slots__ = ()

    def append(self, child: C) -> C:
        """Append a child element or text node and return it.

        An element that already has a parent is moved. Elements referenced by
        the child but not yet placed are collected into the root ``<defs>``.

        Parameters
        ----------
        child : Element or str
            The child to append.

        Returns
        -------
        Element or str
            The appended child.

        Raises
        ------
        TypeError
            If the content model forbids the child, or it is not an element or str.

        See Also
        --------
        insert : Add a child at a given position.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group()
        >>> g.append(svg.circle(0, 0, 1)).tag
        'circle'
        """
        from ._element import Element

        if isinstance(child, str):
            if ContentModel.TEXT not in self.content:
                raise TypeError(f"<{self.tag}> cannot contain text")
        elif isinstance(child, Element):
            if ContentModel.ELEMENTS not in self.content:
                raise TypeError(f"<{self.tag}> cannot contain elements")
            if child.parent is not None:
                child.parent.remove(child)
            child.parent = self
            from ...._internal._page import adopt_page_lengths, page_unit

            adopt_page_lengths(child, page_unit(self))
        else:
            raise TypeError(f"cannot append {type(child).__name__}")
        self.children.append(child)
        if isinstance(child, Element):
            self._define_references(child)
        return child

    def _define_references(self, subtree: Element) -> None:
        """Move unplaced elements referenced from *subtree* into the root's ``<defs>``."""
        root = self.root()
        if root.tag != "svg":
            return
        for element in subtree.iter():
            if element._auto_id and element._id_owner is not root:
                object.__setattr__(element, "_id_owner", root)
                element.attributes["id"] = root._auto_id_for(element.tag or "el", element)
            for target in list(references_of(element)):
                if target.parent is None and target is not root:
                    root.defs().append(target)  # type: ignore[attr-defined]
                elif _foreign_definition(target, root):
                    _point_at_copy(element, target, root)

    def extend(self, children: Iterable[Child]) -> None:
        """Append every child in *children*.

        Parameters
        ----------
        children : iterable of Element or str
            The children to append, in order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group()
        >>> g.extend([svg.circle(0, 0, 1), svg.circle(1, 1, 1)])
        >>> len(g)
        2
        """
        for child in children:
            self.append(child)

    def insert(self, index: int, child: C) -> C:
        """Insert a child at *index* and return it.

        Parameters
        ----------
        index : int
            Position among the children.
        child : Element or str
            The child to insert.

        Returns
        -------
        Element or str
            The inserted child.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1))
        >>> _ = g.insert(0, svg.rect(0, 0, 1, 1))
        >>> [c.tag for c in g]
        ['rect', 'circle']
        """
        self.append(child)
        self.children.insert(index, self.children.pop())
        return child

    def remove(self, child: Child) -> None:
        """Remove a child and detach it from this element.

        Parameters
        ----------
        child : Element or str
            The child to remove.

        Raises
        ------
        ValueError
            If the child is not present.

        Examples
        --------
        >>> import svgwriter as svg
        >>> c = svg.circle(0, 0, 1)
        >>> g = svg.group(c)
        >>> g.remove(c)
        >>> len(g)
        0
        """
        from ._element import Element

        self.children.remove(child)
        if isinstance(child, Element):
            child.parent = None

    def clear(self) -> None:
        """Remove and detach every child.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1))
        >>> g.clear()
        >>> len(g)
        0
        """
        from ._element import Element

        for child in self.children:
            if isinstance(child, Element):
                child.parent = None
        self.children.clear()

    @property
    def text_content(self) -> str:
        """All character data below this element, in document order (the DOM ``textContent``).

        Assigning replaces every child with the single string.

        Examples
        --------
        >>> import svgwriter as svg
        >>> t = svg.text("Hello world")
        >>> t[6:].fill = "red"
        >>> t.text_content
        'Hello world'
        >>> title = svg.Title("Old")
        >>> title.text_content = "New"
        >>> str(title)
        '<title>New</title>'
        """
        return "".join(c if isinstance(c, str) else c.text_content for c in self.children)

    @text_content.setter
    def text_content(self, value: str) -> None:
        self.clear()
        if value:
            self.append(value)  # type: ignore[arg-type]
