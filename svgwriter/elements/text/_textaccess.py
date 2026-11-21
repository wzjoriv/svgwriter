"""
Layout, indexing and run access for ``<text>``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, overload

from ...attributes.names import PRESENTATION_ATTRIBUTES
from ...transform.matrix import Point
from ..core import Element
from ._character import Character, CharacterRange
from ._clusters import cluster_bounds
from ._textlayout import collect, layout

if TYPE_CHECKING:
    from ...ops.text import GlyphBox
    from ...pathdata.data import BBox, PathData
    from ..shapes import Path
    from ..structure import Group
    from ._spans import TSpan
    from ._text import Text


__all__ = ["TextAccess"]


class TextAccess:
    """Characters, layout, runs and glyphs; mixed into :class:`~svgwriter.elements.Text`."""

    __slots__ = ()

    @property
    def characters(self) -> str:
        """The rendered characters as one string.

        All character data (``tspan`` content included) after SVG's ``xml:space``
        handling: newlines dropped, tabs to spaces, runs of spaces collapsed and
        ends trimmed, unless ``xml:space="preserve"``.

        Examples
        --------
        >>> from svgwriter.elements.text import Text
        >>> t = Text("a  b", x=0, y=0)
        >>> span = t.span("c")
        >>> t.characters
        'a bc'
        """
        return "".join(c.char for c in collect(self))

    def _baseline_point(self) -> Point:
        """Start of the first baseline: the first glyph's origin, or ``(0, 0)`` for empty text."""
        boxes = self.layout()
        return Point(boxes[0].x, boxes[0].y) if boxes else Point(0.0, 0.0)

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
        >>> from svgwriter.elements.text import Text
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
        >>> from svgwriter.elements.text import Text
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
        >>> from svgwriter.elements.text import Text
        >>> len(Text("Hi", x=0, y=20).local_outline()) > 0
        True
        """
        from ...pathdata.data import PathData

        return sum((box.placed() for box in self.layout()), PathData())

    def __len__(self) -> int:
        """Number of user-perceived characters (grapheme clusters)."""
        return len(cluster_bounds(self.characters)) - 1

    @overload
    def __getitem__(self, index: int) -> Character: ...
    @overload
    def __getitem__(self, index: slice) -> CharacterRange: ...
    def __getitem__(self, index: int | slice) -> Character | CharacterRange:
        """A live :class:`Character` (``text[i]``) or :class:`CharacterRange` (``text[a:b]``).

        Examples
        --------
        >>> from svgwriter.elements.text import Text
        >>> t = Text("Hello world", x=0, y=20)
        >>> t[-1].char, t[6:].chars, len(t)
        ('d', 'world', 11)
        >>> accented = Text("café!", x=0, y=20)
        >>> len(accented), accented[3].char == "é"
        (5, True)
        """
        bounds = cluster_bounds(self.characters)
        count = len(bounds) - 1
        if isinstance(index, slice):
            start, stop, step = index.indices(count)
            if step != 1:
                raise ValueError("text ranges must be contiguous (step 1)")
            return CharacterRange(self, bounds[start], bounds[max(start, stop)])
        if not -count <= index < count:
            raise IndexError(f"text has {count} characters, index {index} is out of range")
        index %= count
        return Character(self, index, bounds[index], bounds[index + 1])

    def __iter__(self) -> Iterator[Character]:  # type: ignore[override]
        """The characters (grapheme clusters) as :class:`Character` handles; ``children`` holds the runs and spans."""
        bounds = cluster_bounds(self.characters)
        return (Character(self, i, bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1))

    def visible_bbox(self) -> BBox | None:
        """Tight box, in local coordinates, of the characters not hidden with ``visibility="hidden"``.

        Returns
        -------
        BBox or None
            The box, or None when no visible character has an outline.

        See Also
        --------
        svgwriter.CharacterRange.isolate : Leaves a layer whose visible characters are the range.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(200, 40)
        >>> line = doc.text("Hello world", x=0, y=30)
        >>> layer = line[6:11].isolate()
        >>> layer.visible_bbox().x > line.local_bbox().x
        True
        """
        from ._isolate import visible_bbox

        return visible_bbox(self)  # type: ignore[arg-type]

    def effect(self, name: str, /, **options: Any) -> Text:
        """Apply the text effect registered as *name* to the whole text.

        Parameters
        ----------
        name : str
            A text effect: ``"fire"``, ``"ice"``, ``"smoke"``, ``"metal"``, ``"wind"``, ``"snow"``,
            ``"neon"``, ``"glitch"`` or one registered with :func:`svgwriter.preset.text_effect`.
        **options
            The effect's options.

        Returns
        -------
        Text
            This text, styled.

        Raises
        ------
        KeyError
            If no effect has that name; the message suggests the closest names.

        See Also
        --------
        svgwriter.text_effects : The built-in effects.
        svgwriter.CharacterRange.effect : The same for a range of characters.

        Examples
        --------
        >>> import svgwriter as svg
        >>> title = svg.text("Neon", x=0, y=30, font_size=28)
        >>> title.effect("neon", color="deeppink") is title
        True
        """
        from ..._internal._presets import TEXT_EFFECTS

        return TEXT_EFFECTS.get(name)(self, **options)  # type: ignore[no-any-return]

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
        >>> from svgwriter.elements.text import Text
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
        from ..shapes import Path

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
        >>> from svgwriter.elements.text import Text
        >>> t = Text("Hi", x=0, y=20)
        >>> span = t.span("yo", fill="red")
        >>> len(t.runs())
        2
        """
        from ...pathdata.data import PathData

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
        >>> from svgwriter.elements.text import Text
        >>> g = Text("Hi", x=0, y=20, fill="red").glyphs()
        >>> len(g), g[1].get("fill")
        (2, 'red')
        """
        from ..structure import Group

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
        >>> from svgwriter.elements.text import Text
        >>> t = Text("Hello ", x=0, y=20)
        >>> span = t.span("world", fill="red")
        >>> str(span)
        '<tspan fill="red">world</tspan>'
        >>> str(t)
        '<text x="0" y="20">Hello <tspan fill="red">world</tspan></text>'
        """
        from ._spans import TSpan

        return self.append(TSpan(text, **kwargs))
