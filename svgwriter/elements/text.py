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
    from ..pathdata.data import BBox, PathData
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
    """The ``text-decoration`` keywords, combinable with ``|``.

    Pass a member (or a combination) as the ``decoration`` argument of
    :class:`Text`, :class:`TSpan` or :class:`AltGlyph`.

    See Also
    --------
    Text : The element that takes the ``decoration`` argument.

    Examples
    --------
    >>> d = TextDecoration.UNDERLINE | TextDecoration.LINE_THROUGH
    >>> d.svg_value()
    'underline line-through'
    """

    NONE = 0
    UNDERLINE = enum.auto()
    OVERLINE = enum.auto()
    LINE_THROUGH = enum.auto()
    BLINK = enum.auto()

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Format the flags as a ``text-decoration`` attribute value.

        Parameters
        ----------
        precision : int, optional
            Unused; accepted so every attribute value shares one signature.
            Defaults to the library's default precision.

        Returns
        -------
        str
            The space-separated keywords, or ``"none"`` when no flag is set.

        Examples
        --------
        >>> TextDecoration.NONE.svg_value()
        'none'
        >>> TextDecoration.OVERLINE.svg_value()
        'overline'
        """
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
    """``<text>``: a run of graphics text, laid out with the installed fonts.

    The element holds character data and nested ``tspan``, ``tref``, ``textPath``
    and ``altGlyph`` children. Characters can be addressed, moved and outlined
    individually.

    Parameters
    ----------
    *content : str or Element
        Text runs and ``tspan``/``tref``/``textPath``/``altGlyph`` children.
    x, y, dx, dy : length or sequence of length, optional
        Absolute and relative positions; a list positions successive characters.
    rotate : float or sequence of float, optional
        Per-character rotation in degrees.
    text_length : length, optional
        Target advance width of the text.
    length_adjust : {"spacing", "spacingAndGlyphs"}, optional
        How ``text_length`` is met.
    decoration : TextDecoration, optional
        Written as ``text-decoration``.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    TSpan : A styled or repositioned sub-run.
    TextPath : Text laid out along a path.

    Notes
    -----
    Text takes part in boolean operations through its glyph outlines
    (``Rect(0, 0, 100, 40) - Text("Hi", ...)``). ``text[i]`` is a live
    :class:`Glyph` for character *i* (``len(text)`` counts characters);
    :meth:`glyphs` returns one outline path per character. The method
    ``rotate()`` rotates the whole element; the per-character SVG
    ``rotate`` list is ``text.rotate_``.

    Examples
    --------
    >>> str(Text("Hi", x=10, y=20, decoration=TextDecoration.UNDERLINE))
    '<text x="10" y="20" text-decoration="underline">Hi</text>'
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset(
        {"x", "y", "dx", "dy", "rotate", "textLength", "lengthAdjust", "font-family", "font-size",
         "font-weight", "font-style", "text-anchor"}
    )

    @property
    def characters(self) -> str:
        """The rendered characters as one string.

        All character data (``tspan`` content included) after SVG's ``xml:space``
        handling: newlines dropped, tabs to spaces, runs of spaces collapsed and
        ends trimmed, unless ``xml:space="preserve"``.

        Examples
        --------
        >>> t = Text("a  b", x=0, y=0)
        >>> span = t.span("c")
        >>> t.characters
        'a bc'
        """
        return "".join(c.char for c in collect(self))

    def layout(self) -> list[GlyphBox]:
        """Place every character of the text.

        Fonts come from each run's computed style, SVG positioning lists apply
        (innermost ``tspan`` first) and ``text-anchor`` is honoured per text chunk.

        Returns
        -------
        list of GlyphBox
            One box per rendered character.

        Examples
        --------
        >>> boxes = Text("Hi", x=0, y=20).layout()
        >>> len(boxes)
        2
        """
        return layout(self)

    def local_bbox(self) -> BBox | None:
        """Tight box of the glyph outlines in local coordinates.

        Returns
        -------
        BBox or None
            ``None`` when no character has an outline.

        Examples
        --------
        >>> Text("Hi", x=0, y=20).local_bbox() is not None
        True
        """
        return self.local_outline().bbox

    def local_outline(self) -> PathData:
        """Glyph outlines of the text in local coordinates.

        Returns
        -------
        PathData
            All characters' outlines combined.

        Examples
        --------
        >>> len(Text("Hi", x=0, y=20).local_outline()) > 0
        True
        """
        from ..pathdata.data import PathData

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
        """Presentation attributes that apply to glyphs coming from *source*.

        The text's own presentation attributes come first, then those of each
        enclosing ``tspan`` from outermost to innermost, so inner ones win.

        Parameters
        ----------
        source : Element
            The text itself or a descendant run.

        Returns
        -------
        dict
            Attribute names mapped to values.

        Examples
        --------
        >>> t = Text("a", fill="red")
        >>> s = t.span("b", fill="blue")
        >>> t.run_style(t), t.run_style(s)
        ({'fill': 'red'}, {'fill': 'blue'})
        """
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
        """Outline paths split by run.

        Consecutive characters that come from the same element share one
        ``<path>``, styled like that element.

        Returns
        -------
        list of Path
            Outline paths in local coordinates.

        Examples
        --------
        >>> t = Text("Hi", x=0, y=20)
        >>> span = t.span("yo", fill="red")
        >>> len(t.runs())
        2
        """
        from ..pathdata.data import PathData

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
        skip_blank : bool, optional
            Leave out characters without an outline (spaces); otherwise the
            group's children line up with the character indices. Defaults to
            False.

        Returns
        -------
        Group
            A ``<g>`` of outline paths.

        See Also
        --------
        Text.runs : Outlines merged per run instead.

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
        """Append a ``<tspan>`` and return it.

        Parameters
        ----------
        text : str
            The span's character data.
        **kwargs
            Attributes of the :class:`TSpan`.

        Returns
        -------
        TSpan
            The new span, already a child of this text.

        Examples
        --------
        >>> t = Text("Hello ", x=0, y=20)
        >>> span = t.span("world", fill="red")
        >>> str(span)
        '<tspan fill="red">world</tspan>'
        >>> str(t)
        '<text x="0" y="20">Hello <tspan fill="red">world</tspan></text>'
        """
        return self.append(TSpan(text, **kwargs))


class TSpan(PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextLength, _TextPositioning, tag="tspan", category=Category.TEXT_CONTENT, content=ContentModel.MIXED):
    """``<tspan>``: a sub-run of text with its own position or style.

    Parameters
    ----------
    *args : str or Element
        Character data and nested spans.
    x, y, dx, dy : length or sequence of length, optional
        Absolute and relative positions.
    rotate : float or sequence of float, optional
        Per-character rotation in degrees.
    text_length : length, optional
        Target advance width of the run.
    length_adjust : {"spacing", "spacingAndGlyphs"}, optional
        How ``text_length`` is met.
    decoration : TextDecoration, optional
        Written as ``text-decoration``.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Text.span : Append a span to a text.

    Examples
    --------
    >>> str(TSpan("a", dx=3, fill="red"))
    '<tspan dx="3" fill="red">a</tspan>'
    """


class TRef(XLinkAttributes, PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextPositioning, tag="tref", category=Category.TEXT_CONTENT):
    """``<tref>``: the character data of a referenced element.

    Parameters
    ----------
    href : str or Element, optional
        The referenced element, or its IRI.
    x, y, dx, dy : length or sequence of length, optional
        Absolute and relative positions.
    rotate : float or sequence of float, optional
        Per-character rotation in degrees.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    TSpan : A run with its own character data.

    Examples
    --------
    >>> TRef("#label", x=1).get("x")
    1
    """

    def __init__(self, href: str | Element | None = None, **kwargs: Any) -> None:
        super().__init__(href=href, **kwargs)


class TextPath(XLinkAttributes, PresentationAttributes, ConditionalAttributes, CoreAttributes, _TextLength, tag="textPath", category=Category.TEXT_CONTENT, content=ContentModel.MIXED):
    """``<textPath>``: text laid out along a path.

    Parameters
    ----------
    *content : str or Element
        Character data and spans.
    href : str or Element, optional
        The path to follow, or its IRI.
    start_offset : length, optional
        Distance along the path where the text starts.
    method : {"align", "stretch"}, optional
        How glyphs are fitted to the path.
    spacing : {"auto", "exact"}, optional
        How glyph spacing is computed.
    text_length : length, optional
        Target advance width of the text.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Text : Text laid out on a straight baseline.

    Examples
    --------
    >>> TextPath("abc", href="#p", start_offset="50%").get("startOffset")
    '50%'
    """

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
    """``<altGlyph>``: substitute glyphs for its character data.

    Parameters
    ----------
    text : str, optional
        The character data to substitute. Defaults to the empty string.
    href : str or Element, optional
        An ``altGlyphDef`` or a glyph, or its IRI.
    glyph_ref : str, optional
        Identifier of the glyph in the referenced font.
    format : str, optional
        Glyph format of the font.
    x, y, dx, dy : length or sequence of length, optional
        Absolute and relative positions.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    AltGlyphDef : The definition ``href`` points at.

    Examples
    --------
    >>> str(AltGlyph("a", glyph_ref="g1"))
    '<altGlyph glyphRef="g1">a</altGlyph>'
    """

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
    """``<glyphRef>``: one glyph of an ``altGlyphDef``.

    Parameters
    ----------
    href : str or Element, optional
        The glyph, or its IRI.
    glyph_ref : str, optional
        Identifier of the glyph in the font.
    format : str, optional
        Glyph format of the font.
    x, y, dx, dy : float, optional
        Position and offset of the glyph.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    AltGlyphItem : Groups glyph references into one candidate set.

    Examples
    --------
    >>> GlyphRef("#g", x=1).get("x")
    1
    """

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
    """``<altGlyphItem>``: one candidate set of glyph references.

    Parameters
    ----------
    *children : GlyphRef
        The glyph references of the candidate.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    AltGlyphDef : The container of candidates.

    Examples
    --------
    >>> len(AltGlyphItem(GlyphRef("#a"), GlyphRef("#b")))
    2
    """


class AltGlyphDef(CoreAttributes, Container[Element], tag="altGlyphDef", category=Category.TEXT_CONTENT):
    """``<altGlyphDef>``: glyph substitutions for ``altGlyph``.

    Parameters
    ----------
    *children : Element
        Either one sequence of :class:`GlyphRef` or several :class:`AltGlyphItem`.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    AltGlyph : The element that uses the definition.

    Examples
    --------
    >>> len(AltGlyphDef(AltGlyphItem(GlyphRef("#a"))))
    1
    """
