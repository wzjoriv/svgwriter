"""``Document``: a root ``<svg>`` plus a cursor for nested building."""

from __future__ import annotations

import enum
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
from .path.data import BBox
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
    """Anything with a ``_repr_svg_`` (the IPython display protocol)."""

    def _repr_svg_(self) -> str | None: ...


def _ingest(item: Any) -> Any:
    """Elements and iterables pass through; ``_repr_svg_`` objects become a ``<g>`` holding their ``<svg>``."""
    if isinstance(item, Element) or not hasattr(item, "_repr_svg_"):
        return item
    from .io.parser import parse

    text = item._repr_svg_()
    if not text:
        raise TypeError(f"{type(item).__name__}._repr_svg_() returned no SVG")
    root = parse(text)

    for key in ("version", "baseProfile"):
        root.attributes.pop(key, None)
    return Group(root)

E = TypeVar("E", bound=Element)


class ShapeKind(str, enum.Enum):
    """Shape names accepted by :meth:`Document.add_shape`."""

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
    root : Svg, optional
        Use an existing root instead of creating one.
    **kwargs
        Forwarded to :class:`~svgwriter.elements.Svg`.

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
        from .io.parser import Strictness, parse

        root = parse(text, strictness=strictness or Strictness.LENIENT)
        if not isinstance(root, Svg):
            raise ValueError(f"root element is <{root.tag}>, not <svg>")
        return cls(root=root)

    @classmethod
    def from_file(cls, path: AnyPath) -> Document:
        with open(path, "rb") as handle:
            return cls.from_string(handle.read())

    @classmethod
    @contextmanager
    def writing(cls, path: AnyPath, width: float, height: float, **kwargs: Any) -> Iterator[Document]:
        """Build a document and save it to *path* when the block exits."""
        options = kwargs.pop("options", None)
        doc = cls(width, height, **kwargs)
        yield doc
        doc.save(path, options=options)

    @property
    def current(self) -> Element:
        """Where :meth:`add` inserts: the innermost open container."""
        return self._stack.peek()

    @property
    def defs(self) -> Defs:
        """The root ``<defs>``, created on first use; ``doc.defs += x`` adds to it."""
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
        """
        return self._place(_ingest(element))  # type: ignore[arg-type]

    def define(self, element: E) -> E:
        """Put *element* in ``<defs>`` (giving it an id) and return it."""
        return self._define(element)

    def title(self, text: str) -> Title:
        return self.root.insert(0, Title(text))

    def describe(self, text: str) -> Desc:
        return self.add(Desc(text))

    def style(self, css: str | StyleSheet = "", **kwargs: Any) -> StyleElement:
        """Add a ``<style>`` sheet near the top of the document."""
        from .elements.structure import StyleElement

        return self.root.insert(1 if self.root.children and isinstance(self.root.children[0], Title) else 0, StyleElement(css, **kwargs))

    @contextmanager
    def nest(self, element: E) -> Iterator[E]:
        """Add *element* and make it the insertion point inside the block."""
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
        """Create a shape by name, forwarding keywords to its class."""
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

        Raises
        ------
        IndexError, KeyError
            When nothing is at that position or has that id.
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
        return self.root.get_element_by_id(element_id)

    @property
    def auto_size(self) -> bool:
        """Whether the canvas is computed from the content (no ``width``, ``height`` or ``viewBox`` set)."""
        root = self.root
        return root.get("width") is None and root.get("height") is None and root.view_box is None

    def content_bounds(self, padding: float = 0.0) -> BBox | None:
        """Union of the top-level content's stroke-inclusive bounds, grown by *padding*."""
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
        """Set ``viewBox``, ``width`` and ``height`` to the content bounds (plus *padding*) and return ``self``."""
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
        """Serialize; see :class:`svgwriter.io.SerializeOptions`. Auto-sized documents get their size here."""
        with self._sized():
            return self.root.to_string(**options)

    def __str__(self) -> str:
        return self.to_string(xml_declaration=False)

    def _repr_svg_(self) -> str:
        return self.to_string(xml_declaration=False)

    def _repr_png_(self) -> bytes:
        return self.render_png()

    def rasterize(self, *, scale: float = 1.0, size: tuple[int, int] | None = None,
                  background: str | None = None) -> np.ndarray:
        """Render into a float32 RGBA array (see :func:`svgwriter.ops.rasterize`)."""
        from .ops.render import rasterize

        with self._sized():
            return rasterize(self, scale=scale, size=size, background=background)

    def render_png(self, *, scale: float = 1.0, background: str | None = None) -> bytes:
        """Render to PNG bytes."""
        from .ops.render import encode

        return encode(self.rasterize(scale=scale, background=background))

    def save(self, target: AnyPath | TextSink, **options: Any) -> None:
        with self._sized():
            self.root.save(target, **options)

    async def save_async(self, path: AnyPath, **options: Any) -> None:
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
        Raises :class:`~svgwriter.video.FFmpegNotFoundError` before doing
        any work when ffmpeg is missing.
        """
        from .video.animation import render_animation

        return render_animation(self, path, fps, duration, renderer, update=update, ffmpeg=ffmpeg)
