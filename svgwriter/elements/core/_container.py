"""
Typed child lists, composition operators and nestable containers.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import AbstractContextManager
from types import TracebackType
from typing import TYPE_CHECKING, Generic, TypeVar, overload

from ..._internal._tree import attach_cursor, cursor_of, element_list
from ..._internal._typing import Self
from ._element import Element
from ._factory import ElementFactory

if TYPE_CHECKING:
    from ..structure import Defs

__all__ = ["ChildT", "Container", "GraphicsContainer", "Insertable"]

ChildT = TypeVar("ChildT", bound=Element)
E = TypeVar("E", bound=Element)

Insertable = Element | str | Iterable[Element]

class Container(Element, Generic[ChildT]):
    """Adds typed ``add``/iteration and ``+=`` for elements with a known child type.

    Examples
    --------
    >>> import svgwriter as svg
    >>> g = svg.group()
    >>> g += [svg.circle(0, 0, 1), svg.rect(0, 0, 1, 1)]
    >>> len(g), g[0].tag
    (2, 'circle')
    """

    def add(self, child: ChildT) -> ChildT:
        """Append a child and return it.

        Parameters
        ----------
        child : Element
            The child to append.

        Returns
        -------
        Element
            The appended child.

        See Also
        --------
        add_all : Append several children.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.group().add(svg.circle(0, 0, 1)).tag
        'circle'
        """
        if not isinstance(child, (Element, str)):
            from ..._document.ingest import to_element

            child = to_element(child)
        return self.append(child)

    def add_all(self, children: Iterable[ChildT]) -> list[ChildT]:
        """Append every child and return them as a list.

        Parameters
        ----------
        children : iterable of Element
            The children to append, in order.

        Returns
        -------
        list of Element
            The appended children.

        Examples
        --------
        >>> import svgwriter as svg
        >>> len(svg.group().add_all([svg.circle(0, 0, 1), svg.circle(1, 1, 1)]))
        2
        """
        return [self.append(child) for child in children]

    def __iadd__(self, children: ChildT | Iterable[ChildT]) -> Self:
        """``container += child`` or ``container += [a, b]`` appends."""
        self.extend(element_list(children))
        return self

    def __iter__(self) -> Iterator[ChildT]:
        return (c for c in self.children if isinstance(c, Element))  # type: ignore[misc]

    @overload
    def __getitem__(self, index: int) -> ChildT: ...
    @overload
    def __getitem__(self, index: slice) -> list[ChildT]: ...
    def __getitem__(self, index: int | slice) -> ChildT | list[ChildT]:
        if not isinstance(index, (int, slice)):
            hint = "; find elements by id with root.get_element_by_id(...)" if isinstance(index, str) else ""
            raise TypeError(f"<{self.tag}> children are indexed by position or slice, not {type(index).__name__}{hint}")
        items = list(self)
        return items[index]

    def __setitem__(self, index: int, element: ChildT) -> None:
        """``group[i] = el``: put *el* where the *i*-th child element is."""
        from ..._internal._tree import replace_in_parent

        replace_in_parent(self[index], element)  # type: ignore[arg-type]


class GraphicsContainer(  # type: ignore[misc]
    ElementFactory,
    AbstractContextManager["GraphicsContainer", None],
    Container[Element],
):
    """Containers of drawable content: shortcuts and ``with`` nesting.

    ``text`` is the :meth:`ElementFactory.text` shortcut here; these
    elements never hold character data.

    See Also
    --------
    svgwriter.elements.Container : Typed child lists.

    Examples
    --------
    >>> import svgwriter as svg
    >>> g = svg.group()
    >>> with g:
    ...     _ = g.circle(5, 5, 2)
    >>> len(g)
    1
    """

    def _place(self, element: E) -> E:
        attach_cursor(element, cursor_of(self))
        return self.append(element)

    def _define(self, element: E) -> E:
        element.ensure_id()
        defs = self.definitions()
        if element.parent is not defs:
            defs.append(element)
        attach_cursor(element, cursor_of(self))
        return element

    def definitions(self) -> Defs:
        """The ``<defs>`` used by definition shortcuts.

        The root ``<svg>``'s when this container is inside one, otherwise a
        ``<defs>`` child of this container.

        Returns
        -------
        Defs
            The existing or newly created ``<defs>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.group().definitions().tag
        'defs'
        """
        from ..structure import Defs, Svg

        root = self.root()
        if isinstance(root, Svg):
            return root.defs()
        if isinstance(self, Defs):
            return self
        for child in self:
            if isinstance(child, Defs):
                return child
        return self.insert(0, Defs())

    def __enter__(self) -> Self:
        stack = cursor_of(self)
        if stack is not None:
            stack.push(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        stack = cursor_of(self)
        if stack is not None and stack and stack.peek() is self:
            stack.pop()
