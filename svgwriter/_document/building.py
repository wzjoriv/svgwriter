"""
Building a document: the insertion point, ``<defs>``, adding, defining and nesting elements.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, TypeVar, overload

from .._internal._tree import attach_cursor
from ..model.elements.core import Element
from ..model.elements.structure import Desc, Title
from .ingest import SupportsSVG, to_element

if TYPE_CHECKING:
    from .._internal._typing import Stack
    from ..model.attributes.style import StyleSheet
    from ..model.elements.structure import Defs, Group, StyleElement, Svg

__all__ = ["Building"]

E = TypeVar("E", bound=Element)


class Building:
    """The insertion point and the ways to add elements; mixed into :class:`~svgwriter.Document`."""

    root: Svg
    _stack: Stack[Element]

    @property
    def current(self) -> Element:
        """Where :meth:`add` inserts: the innermost open container.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> doc.current is doc.root
        True
        >>> with doc.group() as g:
        ...     print(doc.current is g)
        True
        """
        return self._stack.peek()

    @property
    def defs(self) -> Defs:
        """The root ``<defs>``, created on first use; ``doc.defs += x`` adds to it.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> doc.defs += svg.Rect(0, 0, 1, 1, id="cell")
        >>> doc.defs.tag, len(doc.defs)
        ('defs', 1)
        """
        return self.root.defs()

    @defs.setter
    def defs(self, value: Defs) -> None:
        if value is not self.root.defs():
            raise AttributeError("use doc.defs += element to add definitions")

    def _place(self, element: E) -> E:
        attach_cursor(element, self._stack)
        return self.current.append(element)

    def _define(self, element: E) -> E:
        element.ensure_id()
        if element.parent is not self.defs:
            self.defs.append(element)
        attach_cursor(element, self._stack)
        return element

    @overload
    def add(self, element: E) -> E: ...
    @overload
    def add(self, element: SupportsSVG) -> Group: ...
    def add(self, element: Element | SupportsSVG) -> Element:
        """Add *element* at the insertion point and return it.

        Objects from other libraries that implement ``_repr_svg_`` (plots,
        diagrams, formulas) are parsed and added as a ``<g>`` holding their
        ``<svg>``, so they can be moved and scaled like any group.

        Parameters
        ----------
        element : Element or SupportsSVG
            The element, or an object providing ``_repr_svg_``.

        Returns
        -------
        Element
            The added element; a ``<g>`` when a foreign object was converted.

        Raises
        ------
        TypeError
            If a ``_repr_svg_`` object returns no SVG.

        See Also
        --------
        define : Add to ``<defs>`` instead.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> rect = doc.add(svg.Rect(0, 0, 5, 5))
        >>> rect.parent is doc.root
        True
        """
        return self._place(to_element(element))  # type: ignore[arg-type]

    def define(self, element: E) -> E:
        """Put *element* in ``<defs>`` (giving it an id) and return it.

        Parameters
        ----------
        element : Element
            The element to define; it receives an id if it has none.

        Returns
        -------
        Element
            The same element, now inside ``<defs>``.

        See Also
        --------
        add : Add at the insertion point instead.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> cell = doc.define(svg.Rect(0, 0, 1, 1))
        >>> cell.parent is doc.defs, cell.id.startswith("rect")
        (True, True)
        """
        return self._define(element)

    def title(self, text: str) -> Title:
        """Add a ``<title>`` as the first child of the root.

        Parameters
        ----------
        text : str
            The accessible name of the document.

        Returns
        -------
        Title
            The new element.

        See Also
        --------
        describe : Add a longer description.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> doc.title("Chart").children
        ['Chart']
        """
        return self.root.insert(0, Title(text))

    def describe(self, text: str) -> Desc:
        """Add a ``<desc>`` at the insertion point.

        Parameters
        ----------
        text : str
            The description.

        Returns
        -------
        Desc
            The new element.

        See Also
        --------
        title : Add a short name.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> doc.describe("A blue square").children
        ['A blue square']
        """
        return self.add(Desc(text))

    def style(self, css: str | StyleSheet = "", **kwargs: Any) -> StyleElement:
        """Add a ``<style>`` sheet near the top of the document.

        Parameters
        ----------
        css : str or StyleSheet, optional
            The stylesheet. Defaults to an empty string.
        **kwargs
            Forwarded to :class:`~svgwriter.model.elements.structure.StyleElement`.

        Returns
        -------
        StyleElement
            The new element, placed after the ``<title>`` when there is one.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> doc.style(".a { fill: red }").tag
        'style'
        """
        from ..model.elements.structure import StyleElement

        return self.root.insert(1 if self.root.children and isinstance(self.root.children[0], Title) else 0, StyleElement(css, **kwargs))

    @contextmanager
    def nest(self, element: E) -> Generator[E, None, None]:
        """Add *element* and make it the insertion point inside the block.

        Parameters
        ----------
        element : Element
            The container to add and open.

        Yields
        ------
        Element
            The same element.

        See Also
        --------
        add : Add without nesting.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> with doc.nest(svg.Group()) as g:
        ...     _ = doc.circle(5, 5, 2)
        >>> len(g)
        1
        """
        self.add(element)
        self._stack.push(element)
        try:
            yield element
        finally:
            self._stack.pop()
