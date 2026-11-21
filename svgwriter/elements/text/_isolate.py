"""
Isolating characters of a ``<text>`` on a layer of their own, and text effects by name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._textlayout import collect

if TYPE_CHECKING:
    from ...pathdata.data import BBox
    from ._text import Text

__all__ = ["RangeEffects", "hide", "isolate", "visible_bbox"]

HIDDEN = "hidden"


def hide(text: Text, start: int, stop: int) -> None:
    """Wrap characters ``[start, stop)`` of *text* in ``visibility="hidden"`` spans, one per run they cross.

    Hidden characters keep their advance, so the rest of the line does not move.
    """
    from ._character import CharacterRange

    chars = collect(text)
    runs: list[tuple[int, int]] = []
    for index in range(start, stop):
        key = (id(chars[index].chain[0]), chars[index].child)
        if runs and index == runs[-1][1] and (id(chars[runs[-1][0]].chain[0]), chars[runs[-1][0]].child) == key:
            runs[-1] = (runs[-1][0], index + 1)
        else:
            runs.append((index, index + 1))
    for first, last in reversed(runs):
        CharacterRange(text, first, last).wrap(visibility=HIDDEN)


def visible_bbox(text: Text) -> BBox | None:
    """Tight local box of the characters of *text* that are not in a ``visibility="hidden"`` span."""
    from ...pathdata.data import PathData

    shown = [not any(str(element.get("visibility", "")) == HIDDEN for element in char.chain) for char in collect(text)]
    data = sum((box.placed() for box, keep in zip(text.layout(), shown, strict=False) if keep), PathData())
    return data.bbox if len(data) else None


def isolate(text: Text, start: int, stop: int) -> Text:
    """Move characters ``[start, stop)`` of *text* onto a copy placed just above it, and return the copy."""
    parent = text.parent
    if parent is None:
        raise ValueError("add the text to a document or group before isolating part of it")
    layer = text.clone()
    for element in layer.iter():
        element.attributes.pop("id", None)
    count = len(collect(text))
    hide(layer, stop, count)
    hide(layer, 0, start)
    hide(text, start, stop)
    parent.insert(parent.children.index(text) + 1, layer)
    return layer


class RangeEffects:
    """``isolate`` and ``effect`` for character handles; mixed into :class:`~svgwriter.CharacterRange`."""

    __slots__ = ()

    text: Text
    start: int
    stop: int

    def isolate(self) -> Text:
        """Move these characters onto a copy of the text placed just above it, and return the copy.

        The copy shows only these characters and the original hides them, both with
        ``visibility="hidden"`` so every character keeps its place. Filters, paint and animations set
        on the copy then reach exactly these characters, and everything stays live text.

        Returns
        -------
        Text
            The copy, placed right after the text in its parent.

        Raises
        ------
        ValueError
            If the text has no parent yet.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(200, 40)
        >>> line = doc.text("Hello world", x=0, y=30)
        >>> layer = line[6:11].isolate()
        >>> layer.filter = svg.filters.blur(1)
        >>> str(line)
        '<text x="0" y="30">Hello <tspan visibility="hidden">world</tspan></text>'
        >>> layer.children[0].get("visibility")
        'hidden'
        """
        return isolate(self.text, self.start, self.stop)

    def effect(self, name: str, /, **options: Any) -> Text:
        """Apply the text effect registered as *name* to these characters only.

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
            The layer holding the styled characters (see :meth:`isolate`).

        Raises
        ------
        KeyError
            If no effect has that name; the message suggests the closest names.

        See Also
        --------
        svgwriter.text_effects : The built-in effects.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(240, 50)
        >>> line = doc.text("into the cold night", x=0, y=36, font_size=24)
        >>> layer = line[9:13].effect("ice", animate=False)
        >>> layer.get("filter") is not None
        True
        """
        from ..._internal._presets import TEXT_EFFECTS

        return TEXT_EFFECTS.get(name)(self, **options)
