"""
``Document``: a root ``<svg>`` plus a cursor for nested building.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, TypeVar, overload

from ._document.access import Access
from ._document.ingest import SupportsSVG, to_element
from ._document.output import Output
from ._document.sizes import PageSize, page_size
from ._document.sizing import Sizing
from ._document.theming import Theming
from ._document.typography import Typography
from ._internal._tree import attach_cursor
from ._internal._typing import AnyPath, Stack
from .elements.core import Element, ElementFactory
from .elements.structure import Defs, Desc, Group, Svg, Title
from .theme.theme import Theme

if TYPE_CHECKING:
    from .attributes.length import Length
    from .attributes.style import StyleSheet
    from .elements.structure import StyleElement
    from .io.parser import Strictness

__all__ = ["Document"]


E = TypeVar("E", bound=Element)


class Document(Sizing, Theming, Typography, Output, Access, ElementFactory):
    """An SVG document under construction.

    Shortcut methods (``doc.circle(...)``, ``doc.linear_gradient(...)``)
    build an element, add it and return it; definitions go into ``<defs>``.
    Containers returned by shortcuts nest when used with ``with``.

    Parameters
    ----------
    width, height : float or Length, optional
        Canvas size; a matching ``viewBox`` is added unless one is given.
        Defaults to None, which sizes the canvas from the content on output.
    size : str or PageSize, optional
        A :class:`~svgwriter.PageSize` (``svg.size.a4``), or a named size instead of `width` and `height`: ``"a4"``, ``"letter"``,
        ``"slide-16:9"``, ``"instagram-post"``, ... (see :data:`~svgwriter.size`), with
        ``-landscape`` or ``-portrait`` appended to turn it. Paper sizes are in millimetres or
        inches, so the ``viewBox`` counts in those units. Defaults to None.
    root : Svg, optional
        Use an existing root instead of creating one. Defaults to None.
    theme : Theme or str, optional
        Styles elements marked with ``as_role``. Defaults to None, which takes
        :meth:`Theme.current() <svgwriter.Theme.current>` (``"light"`` outside a ``with theme:`` block).
    **kwargs
        Forwarded to :class:`~svgwriter.elements.Svg`.

    Raises
    ------
    TypeError
        If `size` is given together with `width` or `height`.
    ValueError
        If `size` is not a registered name.

    See Also
    --------
    svgwriter.elements.Svg : The root element wrapped by a document.
    svgwriter.preset.size : Add a named size.

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
    >>> page = Document(size="a4")
    >>> page.root.get("width"), page.root.get("viewBox").width
    (Length(value=210.0, unit=<Unit.MM: 'mm'>), 210.0)
    """

    def __init__(self, width: float | Length | None = None, height: float | Length | None = None, *,
                 size: str | PageSize | None = None, root: Svg | None = None, theme: Theme | str | None = None,
                 **kwargs: Any) -> None:
        if size is not None:
            if width is not None or height is not None:
                raise TypeError("give either size= or width and height, not both")
            width, height = page_size(size)
        if root is None:
            if width is not None and height is not None:
                root = Svg.with_size(width, height, **kwargs)
            else:
                root = Svg(width=width, height=height, **kwargs)
        self.root = root
        self.theme = Theme.of(theme)
        self._stack: Stack[Element] = Stack([root])
        attach_cursor(root, self._stack)

    @classmethod
    def from_string(cls, text: str | bytes, format: str = "svg", *, strictness: Strictness | None = None,
                    **options: Any) -> Document:
        """Parse text in any registered format into a document: SVG by default, or Mermaid, DOT, TikZ, ...

        Text formats that are usually files (``"mermaid"``, ``"dot"``, ``"tikz"``, ``"markdown"``,
        ``"txt"``, ``"eps"``, ...) are read from the string itself, with the same importer as
        :meth:`open`.

        Parameters
        ----------
        text : str or bytes
            The source; ``str`` is encoded as UTF-8 for formats read as bytes.
        format : str, optional
            A registered importer name (see ``svg.export.importers()``). Defaults to ``"svg"``.
        strictness : Strictness, optional
            How SVG treats unknown elements and unsupported attributes. Defaults to
            ``Strictness.LENIENT``. SVG only.
        **options : Any
            Options of the importer (for example ``theme=`` for Mermaid).

        Returns
        -------
        Document
            A document wrapping the parsed root.

        Raises
        ------
        SVGParseError
            If the text is malformed or, when strict, unsupported.
        ValueError
            If the root element is not ``<svg>``, or *format* is not a registered importer.
        TypeError
            If *strictness* is given for a format other than SVG.

        See Also
        --------
        open : Read a file in any registered format.

        Examples
        --------
        >>> doc = Document.from_string('<svg xmlns="http://www.w3.org/2000/svg"><rect width="4" height="4"/></svg>')
        >>> [element.tag for element in doc]
        ['rect']
        >>> chart = Document.from_string("flowchart LR\\n  A --> B", "mermaid")
        >>> len(chart.root.children) > 0
        True
        """
        from .io.parser import Strictness, parse

        if format.lower() != "svg":
            from .export import find_importer

            if strictness is not None:
                raise TypeError("strictness= applies to SVG only")
            try:
                importer = find_importer(format)
            except ValueError:
                importer = find_importer(f"text.{format.lstrip('.')}")
            data = text.encode("utf-8") if isinstance(text, str) else text
            return importer.function(data, **options)  # type: ignore[no-any-return]
        root = parse(text, strictness=strictness or Strictness.LENIENT)
        if not isinstance(root, Svg):
            raise ValueError(f"root element is <{root.tag}>, not <svg>")
        return cls(root=root)

    @classmethod
    @contextmanager
    def writing(cls, path: AnyPath, width: float, height: float, **kwargs: Any) -> Generator[Document, None, None]:
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
