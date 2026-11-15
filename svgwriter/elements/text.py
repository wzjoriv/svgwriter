"""Text content elements."""

from __future__ import annotations

import enum
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias, overload

from .._internal._constants import DEFAULT_PRECISION
from .._internal._typing import LengthAdjust
from ..attributes.length import LengthLike
from ..attributes.names import PRESENTATION_ATTRIBUTES
from ._geometry import PathOperand
from ._glyph import Glyph, GlyphRange
from ._mixins import (
    ConditionalAttributes,
    CoreAttributes,
    GraphicsElement,
    PresentationAttributes,
    XLinkAttributes,
)
from ._textlayout import collect, layout
from .base import Category, Child, ContentModel, Element
from .container import Container

if TYPE_CHECKING:
    from ..ops.text import GlyphBox
    from ..path.data import BBox, PathData
    from .shapes import Path
    from .structure import Group

__all__ = [
    "AltGlyph",
    "AltGlyphDef",
    "AltGlyphItem",
    "GlyphRef",
    "TRef",
    "TSpan",
    "Text",
    "TextDecoration",
    "TextPath",
]

Coordinates: TypeAlias = LengthLike | Sequence[LengthLike]
DEFAULT_FONT_FAMILY = "sans-serif"
DEFAULT_FONT_SIZE = 16.0


class TextDecoration(enum.Flag):
    """``text-decoration`` keywords; combine with ``|``."""

    NONE = 0
    UNDERLINE = enum.auto()
    OVERLINE = enum.auto()
    LINE_THROUGH = enum.auto()
    BLINK = enum.auto()

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        words = [m.name.lower().replace("_", "-") for m in TextDecoration if m.value and m in self]  # type: ignore[union-attr]
        return " ".join(words) or "none"


def _coords(value: Coordinates | None) -> Any:
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return value


class _TextPositioning(Element):
    """``x``, ``y``, ``dx``, ``dy`` and ``rotate``, each a number or list."""

    def __init__(
        self,
        *args: Child,
        x: Coordinates | None = None,
        y: Coordinates | None = None,
        dx: Coordinates | None = None,
        dy: Coordinates | None = None,
        rotate: float | Sequence[float] | None = None,
        **kwargs: Any,
    ) -> None:
        decoration = kwargs.pop("decoration", None)
        super().__init__(*args, **kwargs)
        self.update(x=_coords(x), y=_coords(y), dx=_coords(dx), dy=_coords(dy), rotate=_coords(rotate))
        if decoration is not None:
            self.set("text-decoration", decoration)


class _TextLength(Element):
    def __init__(
        self,
        *args: Child,
        text_length: LengthLike | None = None,
        length_adjust: LengthAdjust | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.update(text_length=text_length, length_adjust=length_adjust)


def _all_text(element: Element) -> str:
    return "".join(c if isinstance(c, str) else _all_text(c) for c in element.children)


class Text(PathOperand, GraphicsElement, _TextLength, _TextPositioning, tag="text", category=Category.TEXT_CONTENT, content=ContentModel.MIXED):
    """``<text>``.

    Parameters
    ----------
    *content : str or Element
        Text runs and ``tspan``/``tref``/``textPath``/``altGlyph`` children.
    **kwargs
        Positioning (``x``, ``y``, ``dx``, ``dy``, ``rotate``),
        ``text_length``, ``decoration`` (a :class:`TextDecoration`) and any
        presentation, conditional or core attribute.

    Examples
    --------
    >>> str(Text("Hi", x=10, y=20, decoration=TextDecoration.UNDERLINE))
    '<text x="10" y="20" text-decoration="underline">Hi</text>'

    Notes
    -----
    Text takes part in boolean operations through its glyph outlines
    (``Rect(0, 0, 100, 40) - Text("Hi", ...)``). ``text[i]`` is a live
    :class:`Glyph` for character *i* (``len(text)`` counts characters);
    :meth:`glyphs` returns one outline path per character. The method
    ``rotate()`` rotates the whole element; the per-character SVG
    ``rotate`` list is ``text.rotate_``.
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset(
        {"x", "y", "dx", "dy", "rotate", "textLength", "lengthAdjust", "font-family", "font-size",
         "font-weight", "font-style", "text-anchor"}
    )

    @property
    def characters(self) -> str:
        """The rendered characters: all character data (``tspan`` content included) after
        SVG's ``xml:space`` handling (newlines dropped, tabs to spaces, runs of spaces
        collapsed, ends trimmed) unless ``xml:space="preserve"``.
        """
        return "".join(c.char for c in collect(self))

    def layout(self) -> list[GlyphBox]:
        """Per-character placement: fonts from each run's computed style, SVG positioning lists
        (innermost ``tspan`` first), ``text-anchor`` per text chunk.
        """
        return layout(self)

    def local_bbox(self) -> BBox | None:
        return self.local_outline().bbox

    def local_outline(self) -> PathData:
        """Glyph outlines of the text in local coordinates."""
        from ..path.data import PathData

        return sum((box.placed() for box in self.layout()), PathData())

    def __len__(self) -> int:
        """Number of characters."""
        return len(self.characters)

    @overload
    def __getitem__(self, index: int) -> Glyph: ...
    @overload
    def __getitem__(self, index: slice) -> GlyphRange: ...
    def __getitem__(self, index: int | slice) -> Glyph | GlyphRange:
        """A live :class:`Glyph` (``text[i]``) or :class:`GlyphRange` (``text[a:b]``).

        Examples
        --------
        >>> t = Text("Hello world", x=0, y=20)
        >>> t[-1].char, t[6:].chars, len(t)
        ('d', 'world', 11)
        """
        count = len(self.characters)
        if isinstance(index, slice):
            start, stop, step = index.indices(count)
            if step != 1:
                raise ValueError("text ranges must be contiguous (step 1)")
            return GlyphRange(self, start, max(start, stop))
        if not -count <= index < count:
            raise IndexError(f"text has {count} characters, index {index} is out of range")
        return Glyph(self, index % count)

    def __iter__(self) -> Iterator[Glyph]:  # type: ignore[override]
        """The characters as :class:`Glyph` handles; ``children`` holds the runs and spans."""
        return (Glyph(self, i) for i in range(len(self.characters)))

    def run_style(self, source: Element) -> dict[str, object]:
        """Presentation attributes for glyphs from *source*: this text's, then each enclosing ``tspan``'s."""
        chain = []
        node: Element | None = source
        while node is not None and node is not self:
            chain.append(node)
            node = node.parent
        style = {k: v for k, v in self.attributes.items()
                 if k in PRESENTATION_ATTRIBUTES and k not in self.geometry_attributes and k != "clip-path"}
        for element in reversed(chain):
            style.update((k, v) for k, v in element.attributes.items()
                         if k in PRESENTATION_ATTRIBUTES and k not in self.geometry_attributes)
        return style

    def _styled_path(self, data: PathData, source: Element | None = None) -> Path:
        from .shapes import Path

        path = Path(data)
        path.attributes.update(self.run_style(source if source is not None else self))
        return path

    def runs(self) -> list[Path]:
        """Outline paths in local coordinates, one per consecutive run with the same source element."""
        from ..path.data import PathData

        paths: list[Path] = []
        current: Element | None = None
        data = PathData()
        for box in self.layout():
            if box.source is not current and len(data):
                paths.append(self._styled_path(data, current))
                data = PathData()
            current = box.source
            data = data + box.placed()
        if len(data):
            paths.append(self._styled_path(data, current))
        return paths

    def glyphs(self, *, skip_blank: bool = False) -> Group:
        """One outline ``<path>`` per character, in a ``<g>`` carrying this text's transform.

        Each path is styled like its run (``tspan`` styles included).

        Parameters
        ----------
        skip_blank : bool
            Leave out characters without an outline (spaces); otherwise the
            group's children line up with the character indices.

        Examples
        --------
        >>> g = Text("Hi", x=0, y=20, fill="red").glyphs()
        >>> len(g), g[1].get("fill")
        (2, 'red')
        """
        from .structure import Group

        group = Group(t=self.t)
        for box in self.layout():
            data = box.placed()
            if skip_blank and not len(data):
                continue
            group.append(self._styled_path(data, box.source))
        return group

    def span(self, text: str, **kwargs: Any) -> TSpan:
        """Append a ``<tspan>`` and return it."""
        return self.append(TSpan(text, **kwargs))


class TSpan(PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextLength, _TextPositioning, tag="tspan", category=Category.TEXT_CONTENT, content=ContentModel.MIXED):
    """``<tspan>``: a sub-run of text with its own position or style."""


class TRef(XLinkAttributes, PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextPositioning, tag="tref", category=Category.TEXT_CONTENT):
    """``<tref>``: the character data of a referenced element."""

    def __init__(self, href: str | Element | None = None, **kwargs: Any) -> None:
        super().__init__(href=href, **kwargs)


class TextPath(XLinkAttributes, PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextLength, tag="textPath", category=Category.TEXT_CONTENT, content=ContentModel.MIXED):
    """``<textPath>``: text laid out along a path."""

    def __init__(
        self,
        *content: Child,
        href: str | Element | None = None,
        start_offset: LengthLike | None = None,
        method: str | None = None,
        spacing: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*content, href=href, **kwargs)
        self.update(start_offset=start_offset, method=method, spacing=spacing)


class AltGlyph(XLinkAttributes, PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextPositioning, tag="altGlyph", category=Category.TEXT_CONTENT, content=ContentModel.TEXT):
    """``<altGlyph>``: substitute glyphs for its character data."""

    def __init__(
        self,
        text: str = "",
        *,
        href: str | Element | None = None,
        glyph_ref: str | None = None,
        format: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*([text] if text else []), href=href, **kwargs)
        self.update(glyph_ref=glyph_ref, format=format)


class GlyphRef(XLinkAttributes, PresentationAttributes, CoreAttributes, tag="glyphRef", category=Category.TEXT_CONTENT, content=ContentModel.EMPTY):
    """``<glyphRef>``: one glyph of an ``altGlyphDef``."""

    def __init__(
        self,
        href: str | Element | None = None,
        *,
        glyph_ref: str | None = None,
        format: str | None = None,
        x: float | None = None,
        y: float | None = None,
        dx: float | None = None,
        dy: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(href=href, **kwargs)
        self.update(glyph_ref=glyph_ref, format=format, x=x, y=y, dx=dx, dy=dy)


class AltGlyphItem(CoreAttributes, Container[GlyphRef], tag="altGlyphItem", category=Category.TEXT_CONTENT):
    """``<altGlyphItem>``: one candidate set of glyph references."""


class AltGlyphDef(CoreAttributes, Container[Element], tag="altGlyphDef", category=Category.TEXT_CONTENT):
    """``<altGlyphDef>``: glyph substitutions for ``altGlyph``."""
