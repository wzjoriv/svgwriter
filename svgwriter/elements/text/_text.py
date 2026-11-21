"""
Text content elements.
"""

from __future__ import annotations

import enum
from typing import Any, ClassVar

from ..._internal._constants import DEFAULT_PRECISION
from ...attributes.length import LengthLike
from .._behavior import (
    ConditionalAttributes,
    CoreAttributes,
    GraphicsElement,
    PathOperand,
    PresentationAttributes,
    XLinkAttributes,
)
from ..core import Category, Child, Container, ContentModel, Element
from ._textaccess import TextAccess
from ._textbase import _TextLength, _TextPositioning

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


class Text(TextAccess, PathOperand, GraphicsElement, _TextLength, _TextPositioning, tag="text", category=Category.TEXT_CONTENT, content=ContentModel.MIXED):
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
    :class:`Character` for character *i* (``len(text)`` counts characters);
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
        self._assign(start_offset=start_offset, method=method, spacing=spacing)


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
        self._assign(glyph_ref=glyph_ref, format=format)


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
        self._assign(glyph_ref=glyph_ref, format=format, x=x, y=y, dx=dx, dy=dy)


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
