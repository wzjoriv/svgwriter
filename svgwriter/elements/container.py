"""
Typed child lists, composition operators and nestable containers.
"""

from __future__ import annotations

import weakref
from collections.abc import Iterable, Iterator
from contextlib import AbstractContextManager
from types import TracebackType
from typing import TYPE_CHECKING, Generic, TypeVar, overload

from .._internal._typing import Self, Stack
from ._factory import ElementFactory
from .base import Element

if TYPE_CHECKING:
    from .structure import Defs

__all__ = ["ChildT", "Container", "GraphicsContainer", "Insertable"]

ChildT = TypeVar("ChildT", bound=Element)
E = TypeVar("E", bound=Element)

Insertable = Element | str | Iterable[Element]

_CURSORS: weakref.WeakKeyDictionary[Element, Stack[Element]] = weakref.WeakKeyDictionary()


def attach_cursor(element: Element, stack: Stack[Element] | None) -> None:
    """Let ``with element:`` move *stack*'s insertion point.

    Parameters
    ----------
    element : Element
        The element used in a ``with`` statement.
    stack : Stack of Element or None
        The insertion stack to move; None does nothing.

    See Also
    --------
    cursor_of : Look up the stack attached to an element.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._stack import Stack
    >>> from svgwriter.elements.container import attach_cursor, cursor_of
    >>> group, stack = svg.group(), Stack()
    >>> attach_cursor(group, stack)
    >>> cursor_of(group) is stack
    True
    """
    if stack is not None:
        _CURSORS[element] = stack


def cursor_of(element: Element) -> Stack[Element] | None:
    """Return the insertion stack attached to *element*, if any.

    Parameters
    ----------
    element : Element
        The element to look up.

    Returns
    -------
    Stack of Element or None
        The stack set by :func:`attach_cursor`, or None.

    See Also
    --------
    attach_cursor : Attach an insertion stack to an element.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.elements.container import cursor_of
    >>> cursor_of(svg.group()) is None
    True
    """
    return _CURSORS.get(element)


def flatten(items: Insertable) -> list[Element | str]:
    """One element, a text run or an iterable of elements, as a list.

    Parameters
    ----------
    items : Element, str or iterable of Element
        What to normalize.

    Returns
    -------
    list
        The items as a list.

    Raises
    ------
    TypeError
        If *items* is not an element, a string or an iterable of elements.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.elements.container import flatten
    >>> len(flatten([svg.circle(0, 0, 1), svg.circle(1, 1, 1)]))
    2
    """
    if isinstance(items, (Element, str)):
        return [items]
    try:
        flat = list(items)
    except TypeError:
        raise TypeError(f"expected an element or an iterable of elements, got {type(items).__name__}") from None
    for item in flat:
        if not isinstance(item, Element):
            raise TypeError(f"expected elements, got {type(item).__name__}")
    return flat  # type: ignore[return-value]


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
        self.extend(flatten(children))
        return self

    def __iter__(self) -> Iterator[ChildT]:
        return (c for c in self.children if isinstance(c, Element))  # type: ignore[misc]

    @overload
    def __getitem__(self, index: int) -> ChildT: ...
    @overload
    def __getitem__(self, index: slice) -> list[ChildT]: ...
    def __getitem__(self, index: int | slice) -> ChildT | list[ChildT]:
        items = list(self)
        return items[index]


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
    svgwriter.elements.container.Container : Typed child lists.

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
        from .structure import Defs, Svg

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
