"""
``Document``: a root ``<svg>`` plus a cursor for nested building.
"""

from __future__ import annotations

import enum
import os
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path as FilePath
from typing import TYPE_CHECKING, Any, Final, Protocol, TypeVar, overload

import numpy as np

from ._internal._typing import AnyPath, Self, Stack
from .elements._factory import ElementFactory
from .elements.base import Element
from .elements.container import attach_cursor, flatten
from .elements.shapes import Circle, Ellipse, Line, Path, Polygon, Polyline, Rect, Shape
from .elements.structure import Defs, Desc, Group, Svg, Title
from .pathdata.data import BBox
from .video.animation import DEFAULT_FPS

if TYPE_CHECKING:
    from .attributes.protocols import TextSink
    from .attributes.style import StyleSheet
    from .elements.structure import StyleElement
    from .io.parser import Strictness
    from .video.animation import Renderer, Update

__all__ = ["Document", "ShapeKind"]

NON_CONTENT: Final = frozenset({"defs", "style", "title", "desc", "metadata"})


class SupportsSVG(Protocol):
    """Anything with a ``_repr_svg_`` (the IPython display protocol).

    Plots, diagrams and formulas from other libraries usually qualify, and can
    be passed to :meth:`Document.add`.

    See Also
    --------
    Document.add : Accepts these objects.

    Examples
    --------
    >>> import svgwriter as svg
    >>> class Dot:
    ...     def _repr_svg_(self):
    ...         return '<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>'
    >>> doc = svg.Document(10, 10)
    >>> doc.add(Dot()) is not None
    True
    >>> "<circle" in str(doc)
    True
    """

    def _repr_svg_(self) -> str | None: ...


def _ingest(item: Any) -> Any:
    """Elements and iterables pass through; ``_repr_svg_`` objects become a ``<g>`` holding their ``<svg>``."""
    if isinstance(item, Element):
        return item
    if hasattr(item, "savefig"):
        import io

        buffer = io.BytesIO()
        item.savefig(buffer, format="svg")
        text = buffer.getvalue().decode("utf-8")
    elif hasattr(item, "_repr_svg_"):
        text = item._repr_svg_()
    else:
        return item
    from .io.parser import parse

    if not text:
        raise TypeError(f"{type(item).__name__}._repr_svg_() returned no SVG")
    root = parse(text)

    for key in ("version", "baseProfile"):
        root.attributes.pop(key, None)
    return Group(root)

E = TypeVar("E", bound=Element)


class ShapeKind(str, enum.Enum):
    """Shape names accepted by :meth:`Document.add_shape`.

    Members are strings, so ``"rect"`` and ``ShapeKind.RECT`` are interchangeable.

    See Also
    --------
    Document.add_shape : Create a shape by name.

    Examples
    --------
    >>> ShapeKind("circle") is ShapeKind.CIRCLE
    True
    """

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> str:
        return name.lower()

    RECT = enum.auto()
    CIRCLE = enum.auto()
    ELLIPSE = enum.auto()
    LINE = enum.auto()
    POLYLINE = enum.auto()
    POLYGON = enum.auto()
    PATH = enum.auto()
    SQUARE = enum.auto()


class Document(ElementFactory):
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
        from_file : Parse from a file.

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
    def from_file(cls, path: AnyPath) -> Document:
        """Parse an SVG file; relative links (images) resolve against its location.

        Parameters
        ----------
        path : str or os.PathLike
            The file to read.

        Returns
        -------
        Document
            A document wrapping the parsed root.

        Raises
        ------
        SVGParseError
            If the content is malformed.
        FileNotFoundError
            If `path` does not exist.

        See Also
        --------
        from_string : Parse from text.
        open : Read any registered input format.

        Examples
        --------
        >>> import tempfile, pathlib
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "a.svg"
        ...     Document(10, 10).save(path)
        ...     print(Document.from_file(path).root.get("width"))
        10
        """
        with open(path, "rb") as handle:
            document = cls.from_string(handle.read())
        document.root._source_path = os.fspath(path)
        return document

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
        ...     print("<circle" in path.read_text())
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

    def add_shape(self, kind: ShapeKind | str, **kwargs: Any) -> Shape:
        """Create a shape by name, forwarding keywords to its class.

        Parameters
        ----------
        kind : ShapeKind or str
            One of ``rect``, ``circle``, ``ellipse``, ``line``, ``polyline``,
            ``polygon``, ``path`` or ``square``.
        **kwargs
            Constructor keywords of the shape's class; ``square`` takes ``size``
            and the polygon kinds take ``points``.

        Returns
        -------
        Shape
            The shape, already added at the insertion point.

        Raises
        ------
        ValueError
            If `kind` is not a shape name.

        See Also
        --------
        add : Add an element you built yourself.

        Examples
        --------
        >>> doc = Document(10, 10)
        >>> doc.add_shape("circle", cx=5, cy=5, r=2).tag
        'circle'
        """
        kind = ShapeKind(kind)
        if kind is ShapeKind.SQUARE:
            size = kwargs.pop("size")
            shape: Shape = Rect.square(size, **kwargs)
        elif kind in (ShapeKind.POLYLINE, ShapeKind.POLYGON):
            points = kwargs.pop("points", ())
            shape = Polygon(points, **kwargs) if kind is ShapeKind.POLYGON else Polyline(points, **kwargs)
        else:
            classes: dict[ShapeKind, type[Shape]] = {
                ShapeKind.RECT: Rect,
                ShapeKind.CIRCLE: Circle,
                ShapeKind.ELLIPSE: Ellipse,
                ShapeKind.LINE: Line,
                ShapeKind.PATH: Path,
            }
            shape = classes[kind](**kwargs)
        return self.add(shape)

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

    @property
    def auto_size(self) -> bool:
        """Whether the canvas is computed from the content (no ``width``, ``height`` or ``viewBox`` set).

        Examples
        --------
        >>> Document().auto_size, Document(10, 10).auto_size
        (True, False)
        """
        root = self.root
        return root.get("width") is None and root.get("height") is None and root.view_box is None

    def content_bounds(self, padding: float = 0.0) -> BBox | None:
        """Union of the top-level content's stroke-inclusive bounds, grown by *padding*.

        Parameters
        ----------
        padding : float, optional
            Margin added on every side. Defaults to 0.0.

        Returns
        -------
        BBox or None
            The bounds, or None when the content has no measurable shape.

        See Also
        --------
        fit : Apply the bounds as the canvas size.

        Examples
        --------
        >>> doc = Document()
        >>> doc.content_bounds() is None
        True
        >>> _ = doc.rect(10, 10, 20, 20)
        >>> doc.content_bounds(padding=2)
        BBox(x=8.0, y=8.0, width=24.0, height=24.0)
        """
        from .elements._convert import Convertible

        box: BBox | None = None
        for element in self:
            part = element.render_bounds() if isinstance(element, Convertible) else None
            if part is not None:
                box = part if box is None else box.union(part)
        if box is None:
            return None
        return BBox(box.x - padding, box.y - padding, box.width + 2 * padding, box.height + 2 * padding)

    def fit(self, padding: float = 0.0) -> Self:
        """Set ``viewBox``, ``width`` and ``height`` to the content bounds (plus *padding*) and return ``self``.

        Parameters
        ----------
        padding : float, optional
            Margin added on every side. Defaults to 0.0.

        Returns
        -------
        Document
            This document, for chaining.

        See Also
        --------
        content_bounds : The bounds that are applied.

        Examples
        --------
        >>> doc = Document()
        >>> _ = doc.rect(10, 10, 20, 20)
        >>> doc.fit(padding=2).root.view_box
        ViewBox(min_x=8.0, min_y=8.0, width=24.0, height=24.0)
        """
        box = self.content_bounds(padding)
        if box is not None:
            self.root.view_box = (box.x, box.y, box.width, box.height)
            self.root.update(width=box.width, height=box.height)
        return self

    @contextmanager
    def _sized(self) -> Iterator[None]:
        if not self.auto_size:
            yield
            return
        saved = dict(self.root.attributes)
        self.fit()
        try:
            yield
        finally:
            self.root.attributes = saved

    def to_string(self, **options: Any) -> str:
        """Serialize; see :class:`svgwriter.io.SerializeOptions`. Auto-sized documents get their size here.

        Parameters
        ----------
        **options
            Fields of :class:`~svgwriter.io.SerializeOptions`.

        Returns
        -------
        str
            The SVG text.

        See Also
        --------
        save : Write to a file or stream.

        Examples
        --------
        >>> doc = Document(10, 10)
        >>> _ = doc.circle(5, 5, 2)
        >>> print(doc.to_string(pretty=False, xml_declaration=False))
        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10" version="1.1"><circle cx="5" cy="5" r="2"/></svg>
        """
        with self._sized():
            return self.root.to_string(**options)

    def __str__(self) -> str:
        return self.to_string(xml_declaration=False)

    def _repr_svg_(self) -> str:
        return self.to_string(xml_declaration=False)

    def _repr_png_(self) -> bytes:
        return self.render_png()

    def rasterize(self, *, scale: float = 1.0, size: tuple[int, int] | None = None, padding: float = 0.0,
                  background: str | None = None, snapshot: bool = False) -> np.ndarray:
        """Render into a float32 RGBA array (see :func:`svgwriter.ops.rasterize`).

        Parameters
        ----------
        scale : float, optional
            Pixels per user unit. Defaults to 1.0.
        size : tuple of int, optional
            Output size in pixels as ``(width, height)``. Defaults to None, which
            uses the document size times `scale`.
        padding : float, optional
            Margin around the content, in user units. Defaults to 0.0.
        background : str, optional
            Background color. Defaults to None (transparent).
        snapshot : bool, optional
            Render a copy of the tree. Defaults to False.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(height, width, 4)``.

        See Also
        --------
        render_png : Encode the result as PNG bytes.

        Examples
        --------
        >>> doc = Document()
        >>> _ = doc.circle(0, 0, 10)
        >>> doc.rasterize(size=(64, 64), padding=2).shape
        (64, 64, 4)
        """
        from .ops.render import rasterize

        with self._sized():
            return rasterize(self, scale=scale, size=size, padding=padding, background=background,
                             snapshot=snapshot)

    def render_png(self, *, scale: float = 1.0, background: str | None = None) -> bytes:
        """Render to PNG bytes.

        Parameters
        ----------
        scale : float, optional
            Pixels per user unit. Defaults to 1.0.
        background : str, optional
            Background color. Defaults to None (transparent).

        Returns
        -------
        bytes
            A PNG file.

        See Also
        --------
        rasterize : The pixels without encoding.

        Examples
        --------
        >>> doc = Document(8, 6)
        >>> doc.render_png()[1:4]
        b'PNG'
        """
        from .ops.render import encode_image

        return encode_image(self.rasterize(scale=scale, background=background, snapshot=True))

    def save(self, target: AnyPath | TextSink, *, format: str | None = None, **options: Any) -> None:
        """Write to a path or text stream; the format follows *format* or the file extension.

        ``.svg`` (and text streams) write SVG text with :class:`~svgwriter.io.SerializeOptions`;
        other extensions use :mod:`svgwriter.export` (``.png``, ``.pdf``, ``.tikz``, ...).

        Parameters
        ----------
        target : str, os.PathLike or TextSink
            Destination path or text stream.
        format : str, optional
            Format name or extension. Defaults to None, which follows the
            extension of `target`, or SVG for streams.
        **options
            Serializer or exporter options.

        See Also
        --------
        export : Return the output instead of writing it.
        to_string : The SVG text.

        Examples
        --------
        >>> doc = Document(10, 10)
        >>> doc.save("figure.pdf")  # doctest: +SKIP
        """
        if format is None and (not isinstance(target, (str, os.PathLike))
                               or str(target).lower().endswith(".svg")):
            with self._sized():
                self.root.save(target, **options)
            return
        from .export import save

        save(self, target, format, **options)  # type: ignore[arg-type]

    def export(self, format: str, **options: Any) -> bytes | str:
        """This document in *format* (``"png"``, ``"pdf"``, ``"tikz"``, ... or an extension).

        See :func:`svgwriter.export.exporters` for the registered formats.

        Parameters
        ----------
        format : str
            Format name or extension.
        **options
            Exporter options.

        Returns
        -------
        bytes or str
            The encoded document; text formats return ``str``.

        See Also
        --------
        save : Write to a file.

        Examples
        --------
        >>> Document(10, 10).export("png")[1:4]
        b'PNG'
        """
        from .export import export

        return export(self, format, **options)

    @classmethod
    def open(cls, path: AnyPath, *, format: str | None = None, **options: Any) -> Document:
        """Read any registered input format (SVG, SVGZ, PNG, JPEG, ...), chosen by extension.

        Parameters
        ----------
        path : str or os.PathLike
            The file to read.
        format : str, optional
            Format name or extension. Defaults to None, which follows the
            extension of `path`.
        **options
            Loader options.

        Returns
        -------
        Document
            The loaded document.

        See Also
        --------
        from_file : SVG only, with fewer dependencies.

        Examples
        --------
        >>> import tempfile, pathlib
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "a.svg"
        ...     Document(10, 10).save(path)
        ...     print(len(Document.open(path)))
        0
        """
        from .export import load

        return load(path, format, **options)

    async def save_async(self, path: AnyPath, **options: Any) -> None:
        """Write the SVG text to *path* in a worker thread.

        Parameters
        ----------
        path : str or os.PathLike
            Destination file.
        **options
            ``options`` or fields of :class:`~svgwriter.io.SerializeOptions`.

        See Also
        --------
        save : The synchronous version.

        Examples
        --------
        >>> import asyncio, tempfile, pathlib
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "a.svg"
        ...     asyncio.run(Document(10, 10).save_async(path))
        ...     print(path.exists())
        True
        """
        from .io._async import write_async

        await write_async(self.root, path, **options)

    def render_animation(
        self,
        path: AnyPath,
        fps: float = DEFAULT_FPS,
        duration: float | None = None,
        renderer: Renderer | str | None = None,
        *,
        update: Update | None = None,
        ffmpeg: str | None = None,
    ) -> FilePath:
        """Render frames through *renderer* and encode them with ffmpeg.

        See :func:`svgwriter.video.render_animation` for the parameters.
        ffmpeg is located before any frame is rendered.

        Parameters
        ----------
        path : str or os.PathLike
            Output file; the extension picks the encoder.
        fps : float, optional
            Frames per second. Defaults to 30.0.
        duration : float, optional
            Seconds to render. Defaults to the end of the document's SMIL animations.
        renderer : callable or str, optional
            A renderer, a registered name such as ``"skia"`` or ``"module:function"``.
            Defaults to None, which raises; there is no default renderer.
        update : callable, optional
            ``update(document, seconds)`` called before each frame. Defaults to None.
        ffmpeg : str, optional
            The ffmpeg executable. Defaults to ``ffmpeg`` found on ``PATH``.

        Returns
        -------
        pathlib.Path
            The written file.

        Raises
        ------
        FFmpegNotFoundError
            When ffmpeg is missing.
        FFmpegError
            When ffmpeg fails.

        See Also
        --------
        svgwriter.video.iter_frames : The frames without encoding.

        Examples
        --------
        >>> doc = Document(8, 6)
        >>> doc.render_animation("out.gif", duration=1, renderer="skia")  # doctest: +SKIP
        """
        from .video.animation import render_animation

        return render_animation(self, path, fps, duration, renderer, update=update, ffmpeg=ffmpeg)
