"""
Child editing for ``Element``: append, insert, remove and text content.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from ._categories import ContentModel

if TYPE_CHECKING:
    from .base import C, Child, Element


class TreeEditing:
    """Adding, inserting and removing children; mixed into :class:`~svgwriter.elements.base.Element`."""

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
        from .base import Element
        if isinstance(child, str):
            if ContentModel.TEXT not in self.content:
                raise TypeError(f"<{self.tag}> cannot contain text")
        elif isinstance(child, Element):
            if ContentModel.ELEMENTS not in self.content:
                raise TypeError(f"<{self.tag}> cannot contain elements")
            if child.parent is not None:
                child.parent.remove(child)
            child.parent = self
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
            for value in list(element.attributes.values()):
                target = getattr(value, "element", None)
                if target is not None and target.parent is None and target is not root:
                    root.defs().append(target)  # type: ignore[attr-defined]

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
        from .base import Element
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
        from .base import Element
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
