"""Text content elements."""

from __future__ import annotations

import enum
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias

from .._internal._constants import DEFAULT_PRECISION
from .._internal._typing import LengthAdjust
from ..attributes.cascade import Rule, computed, rules_of
from ..attributes.length import Length, LengthLike
from ._geometry import PathOperand
from ._glyph import Glyph, number_list
from ._mixins import (
    ConditionalAttributes,
    CoreAttributes,
    GraphicsElement,
    PresentationAttributes,
    XLinkAttributes,
)
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


def _first(value: Any) -> float:
    if isinstance(value, (list, tuple)):
        value = value[0] if value else 0
    elif isinstance(value, str):
        value = value.replace(",", " ").split()[0] if value.strip() else 0
    return 0.0 if value is None else Length.parse(value).to_user_units()


FONT_WEIGHTS = {"normal": 400, "bold": 700, "bolder": 700, "lighter": 300}
FONT_SIZE_KEYWORDS = {"xx-small": 9.0, "x-small": 10.0, "small": 13.0, "medium": 16.0, "large": 18.0,
                      "x-large": 24.0, "xx-large": 32.0, "smaller": 13.0, "larger": 19.0}


def _font_weight(value: object) -> int:
    text = str(value).strip()
    return FONT_WEIGHTS.get(text, int(text) if text.isdigit() else FONT_WEIGHTS["normal"])


def _font_size(value: object) -> float:
    text = str(value).strip()
    if text in FONT_SIZE_KEYWORDS:
        return FONT_SIZE_KEYWORDS[text]
    try:
        size = Length.parse(value)
    except ValueError:
        return DEFAULT_FONT_SIZE
    return size.value * DEFAULT_FONT_SIZE / 100 if size.unit.value == "%" else size.to_user_units()


def _viewport(element: Element) -> tuple[float, float]:
    root = element.root()
    box = getattr(root, "view_box", None)
    return (box.width, box.height) if box else (0.0, 0.0)


_PRESERVE = {10: " ", 13: " ", 9: " "}
_DEFAULT = {10: None, 13: None, 9: " "}


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
        raw = _all_text(self)
        if str(computed(self, "xml:space", "default", self._rules())) == "preserve":
            return raw.translate(_PRESERVE)
        return " ".join(raw.translate(_DEFAULT).split())

    def _rules(self) -> list[Rule]:
        root = self.root()
        return rules_of(root) if root is not self else []

    def layout(self) -> list[GlyphBox]:
        """Per-character placement (skia fonts, SVG ``x``/``y``/``dx``/``dy``/``rotate`` rules).

        Font properties are computed (CSS and inheritance applied).
        ``tspan`` positioning and styling are not applied yet.
        """
        from ..ops.text import layout_glyphs

        rules = self._rules()

        def style(name: str, default: object) -> object:
            return computed(self, name, default, rules)

        width, height = _viewport(self)
        size = _font_size(style("font-size", DEFAULT_FONT_SIZE))
        return layout_glyphs(
            self.characters,
            str(style("font-family", DEFAULT_FONT_FAMILY)),
            size,
            x=number_list(self.get("x"), width) or [0.0],
            y=number_list(self.get("y"), height) or [0.0],
            dx=number_list(self.get("dx"), width),
            dy=number_list(self.get("dy"), height),
            rotate=number_list(self.get("rotate")),
            anchor=str(style("text-anchor", "start")),  # type: ignore[arg-type]
            weight=_font_weight(style("font-weight", "normal")),
            italic=str(style("font-style", "")) in ("italic", "oblique"),
        )

    def local_bbox(self) -> BBox | None:
        return self.local_outline().bbox

    def local_outline(self) -> PathData:
        """Glyph outlines of the text in local coordinates."""
        from ..path.data import PathData

        return sum((box.placed() for box in self.layout()), PathData())

    def __len__(self) -> int:
        """Number of characters."""
        return len(self.characters)

    def __getitem__(self, index: int) -> Glyph:
        """A live :class:`Glyph` handle on one character.

        Examples
        --------
        >>> t = Text("Hello", x=0, y=20)
        >>> t[-1].char, len(t)
        ('o', 5)
        """
        count = len(self.characters)
        if not -count <= index < count:
            raise IndexError(f"text has {count} characters, index {index} is out of range")
        return Glyph(self, index % count)

    def __iter__(self) -> Iterator[Glyph]:  # type: ignore[override]
        """The characters as :class:`Glyph` handles; ``children`` holds the runs and spans."""
        return (Glyph(self, i) for i in range(len(self.characters)))

    def _styled_path(self, data: PathData) -> Path:
        from .shapes import Path

        path = Path(data)
        path.attributes.update(
            (k, v) for k, v in self.attributes.items()
            if k not in ("id", "transform", "clip-path") and k not in self.geometry_attributes
        )
        return path

    def glyphs(self, *, skip_blank: bool = False) -> Group:
        """One outline ``<path>`` per character, in a ``<g>`` carrying this text's transform.

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
            group.append(self._styled_path(data))
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
