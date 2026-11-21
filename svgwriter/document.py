"""
``Document``: a root ``<svg>`` plus a cursor for nested building.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, TypeVar

from ._document.access import Access
from ._document.building import Building
from ._document.inkscape import InkscapeData
from ._document.output import Output
from ._document.sizes import PageSize, page_size
from ._document.sizing import Sizing
from ._document.theming import Theming
from ._document.typography import Typography
from ._internal._tree import attach_cursor
from ._internal._typing import AnyPath, Stack
from .elements.core import Element, ElementFactory
from .elements.structure import Svg
from .theme.sheet import sheet_theme
from .theme.theme import Theme

if TYPE_CHECKING:
    from .attributes.length import Length
    from .io.parser import Strictness

__all__ = ["Document"]


E = TypeVar("E", bound=Element)


class Document(Building, Sizing, Theming, Typography, Output, Access, InkscapeData, ElementFactory):
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
        Styles elements marked with ``as_role``. Defaults to None, which keeps the theme that wrote
        the theme sheet of an existing `root`, else takes :meth:`Theme.current() <svgwriter.Theme.current>`
        (``"light"`` outside a ``with theme:`` block).
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
        self.theme = Theme.of(theme) if theme is not None else sheet_theme(root) or Theme.current()
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
            Options of the importer (for example ``theme=`` for Mermaid). SVG takes only ``theme=``, the
            theme to restyle the document with (by default the one that wrote it is kept).

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
            If *strictness* is given for a format other than SVG, or SVG is given an option other
            than ``theme``.

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
        theme = options.pop("theme", None)
        if options:
            raise TypeError(f"SVG takes no option {', '.join(map(repr, sorted(options)))}; only theme=")
        root = parse(text, strictness=strictness or Strictness.LENIENT)
        if not isinstance(root, Svg):
            raise ValueError(f"root element is <{root.tag}>, not <svg>")
        return cls(root=root, theme=theme)

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
