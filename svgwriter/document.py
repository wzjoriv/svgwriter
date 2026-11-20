"""
``Document``: a root ``<svg>`` plus a cursor for nested building.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Final, TypeVar, overload

from ._document.ingest import SupportsSVG, _ingest
from ._document.output import Output
from ._document.sizing import Sizing
from ._internal._typing import AnyPath, Self, Stack
from .elements._factory import ElementFactory
from .elements.base import Element
from .elements.container import attach_cursor, flatten
from .elements.structure import Defs, Desc, Group, Svg, Title

if TYPE_CHECKING:
    from .attributes.style import StyleSheet
    from .elements.structure import StyleElement
    from .io.parser import Strictness

__all__ = ["Document"]

NON_CONTENT: Final = frozenset({"defs", "style", "title", "desc", "metadata"})


E = TypeVar("E", bound=Element)


class Document(Sizing, Output, ElementFactory):
    """An SVG document under construction.

    Shortcut methods (``doc.circle(...)``, ``doc.linear_gradient(...)``)
    build an element, add it and return it; definitions go into ``<defs>``.
    Containers returned by shortcuts nest when used with ``with``.

    Parameters
    ----------
    width, height : float, optional
        Canvas size; a matching ``viewBox`` is added unless one is given.
        Defaults to None, which sizes the canvas from the content on output.
    root : Svg, optional
        Use an existing root instead of creating one. Defaults to None.
    **kwargs
        Forwarded to :class:`~svgwriter.elements.Svg`.

    See Also
    --------
    svgwriter.elements.Svg : The root element wrapped by a document.

    Notes
    -----
    ``doc += element`` (or a list) adds at the insertion point. Elements
    used as references (``fill=gradient``, ``clip_path=clip``) go into
    ``<defs>`` automatically; ``doc.define(x)`` or ``doc.defs += x`` does it
    explicitly.

    Examples
    --------
    >>> from svgwriter import Rect
    >>> doc = Document(100, 100)
    >>> glow = doc.radial_gradient(cx=0.5, cy=0.5, r=0.5)
    >>> with doc.group(fill="red") as g:
    ...     _ = doc.rect(10, 10, 20, 20)
    ...     _ = doc.circle(50, 50, 10, fill=glow)
    >>> len(g)
    2
    >>> doc += Rect(0, 0, 5, 5)
    >>> doc.root[-1].tag
    'rect'
    """

    def __init__(self, width: float | None = None, height: float | None = None, *, root: Svg | None = None, **kwargs: Any) -> None:
        if root is None:
            if width is not None and height is not None:
                root = Svg.with_size(width, height, **kwargs)
            else:
                root = Svg(width=width, height=height, **kwargs)
        self.root = root
        self._stack: Stack[Element] = Stack([root])
        attach_cursor(root, self._stack)

    @classmethod
    def from_string(cls, text: str | bytes, *, strictness: Strictness | None = None) -> Document:
        """Parse SVG text into a document.

        Parameters
        ----------
        text : str or bytes
            The SVG source.
        strictness : Strictness, optional
            How to treat unknown elements and unsupported attributes. Defaults to
            ``Strictness.LENIENT``.

        Returns
        -------
        Document
            A document wrapping the parsed root.

        Raises
        ------
        SVGParseError
            If the text is malformed or, when strict, unsupported.
        ValueError
            If the root element is not ``<svg>``.

        See Also
        --------
        open : Read a file in any registered format.

        Examples
        --------
        >>> doc = Document.from_string('<svg xmlns="http://www.w3.org/2000/svg"><rect width="4" height="4"/></svg>')
        >>> [element.tag for element in doc]
        ['rect']
        """
        from .io.parser import Strictness, parse

        root = parse(text, strictness=strictness or Strictness.LENIENT)
        if not isinstance(root, Svg):
            raise ValueError(f"root element is <{root.tag}>, not <svg>")
        return cls(root=root)

    @classmethod
    @contextmanager
    def writing(cls, path: AnyPath, width: float, height: float, **kwargs: Any) -> Iterator[Document]:
        """Build a document and save it to *path* when the block exits.

        Parameters
        ----------
        path : str or os.PathLike
            Where to save the document.
        width, height : float
            Canvas size.
        **kwargs
            Forwarded to the constructor; ``options`` (a
            :class:`~svgwriter.io.SerializeOptions`) is used when saving.

        Yields
        ------
        Document
            The document to draw into.

        See Also
        --------
        save : Save an existing document.

        Examples
        --------
        >>> import tempfile, pathlib
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "a.svg"
        ...     with Document.writing(path, 10, 10) as doc:
        ...         _ = doc.circle(5, 5, 2)
        ...     print("<circle" in path.read_text(encoding="utf-8"))
        True
        """
        options = kwargs.pop("options", None)
        doc = cls(width, height, **kwargs)
        yield doc
        doc.save(path, options=options)

    @property
    def current(self) -> Element:
        """Where :meth:`add` inserts: the innermost open container.

        Examples
        --------
        >>> doc = Document(10, 10)
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
        >>> from svgwriter import Rect
        >>> doc = Document(10, 10)
        >>> doc.defs += Rect(0, 0, 1, 1, id="cell")
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
        >>> from svgwriter import Rect
        >>> doc = Document(10, 10)
        >>> rect = doc.add(Rect(0, 0, 5, 5))
        >>> rect.parent is doc.root
        True
        """
        return self._place(_ingest(element))  # type: ignore[arg-type]

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
        >>> from svgwriter import Rect
        >>> doc = Document(10, 10)
        >>> cell = doc.define(Rect(0, 0, 1, 1))
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
        >>> doc = Document(10, 10)
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
        >>> doc = Document(10, 10)
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
            Forwarded to :class:`~svgwriter.elements.structure.StyleElement`.

        Returns
        -------
        StyleElement
            The new element, placed after the ``<title>`` when there is one.

        Examples
        --------
        >>> doc = Document(10, 10)
        >>> doc.style(".a { fill: red }").tag
        'style'
        """
        from .elements.structure import StyleElement

        return self.root.insert(1 if self.root.children and isinstance(self.root.children[0], Title) else 0, StyleElement(css, **kwargs))

    @contextmanager
    def nest(self, element: E) -> Iterator[E]:
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
        >>> from svgwriter import Group
        >>> doc = Document(10, 10)
        >>> with doc.nest(Group()) as g:
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

    def __iadd__(self, elements: Element | SupportsSVG | Iterable[Element]) -> Self:
        for element in flatten(_ingest(elements)):
            self._place(element)  # type: ignore[type-var]
        return self

    def _content(self) -> list[Element]:
        return [c for c in self.root if c.tag not in NON_CONTENT]

    def __iter__(self) -> Iterator[Element]:
        """Top-level content elements (``<defs>``, ``<style>``, ``<title>``, ``<desc>`` skipped).

        Use ``doc.root.iter()`` to walk the whole tree.
        """
        return iter(self._content())

    def __len__(self) -> int:
        return len(self._content())

    @overload
    def __getitem__(self, key: int) -> Element: ...
    @overload
    def __getitem__(self, key: slice) -> list[Element]: ...
    @overload
    def __getitem__(self, key: str) -> Element: ...
    def __getitem__(self, key: int | slice | str) -> Element | list[Element]:
        """``doc[0]`` (top-level content by position), ``doc[1:3]`` or ``doc["logo"]`` (any element by id).

        Parameters
        ----------
        key : int, slice or str
            A position or slice among the top-level content, or an element id.

        Returns
        -------
        Element or list of Element
            The element, or a list for a slice.

        Raises
        ------
        IndexError, KeyError
            When nothing is at that position or has that id.

        Examples
        --------
        >>> doc = Document(10, 10)
        >>> _ = doc.rect(0, 0, 5, 5, id="logo")
        >>> doc[0] is doc["logo"]
        True
        """
        if isinstance(key, str):
            element = self.root.get_element_by_id(key)
            if element is None:
                raise KeyError(f"no element with id {key!r}")
            return element
        return self._content()[key]

    def __setitem__(self, key: int | str, element: Element) -> None:
        """``doc[0] = el`` or ``doc["logo"] = el``: put *el* where that element is (an explicit id moves to *el*).

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> _ = doc.rect(0, 0, 5, 5, id="logo")
        >>> doc["logo"] = svg.circle(5, 5, 2)
        >>> doc[0].tag, doc[0].id
        ('circle', 'logo')
        """
        from .elements._geometry import replace_in_parent

        replace_in_parent(self[key], _ingest(element))

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return self.root.get_element_by_id(item) is not None
        return isinstance(item, Element) and any(e is item for e in self.root.iter())

    def get_element_by_id(self, element_id: str) -> Element | None:
        """Find an element anywhere in the tree by its id.

        Parameters
        ----------
        element_id : str
            The id to look for.

        Returns
        -------
        Element or None
            The element, or None when no element has that id.

        See Also
        --------
        __getitem__ : ``doc["id"]`` raises instead of returning None.

        Examples
        --------
        >>> doc = Document(10, 10)
        >>> _ = doc.rect(0, 0, 5, 5, id="logo")
        >>> doc.get_element_by_id("logo").tag, doc.get_element_by_id("none")
        ('rect', None)
        """
        return self.root.get_element_by_id(element_id)

