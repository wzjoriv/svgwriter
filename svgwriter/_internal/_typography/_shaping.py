"""
HarfBuzz access for shaping complex scripts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .._constants import (
    CJK_START,
    COMPLEX_SCRIPT_START,
    EMOJI_END,
    EMOJI_JOINERS,
    EMOJI_START,
    LATIN_EXTENDED_ADDITIONAL,
)
from ._fonts import color_font

if TYPE_CHECKING:
    from ...pathdata import PathData

__all__ = ["ColorGlyphs", "harfbuzz", "hb_font", "needs_shaping", "shape_run"]


@dataclass(frozen=True)
class ColorGlyphs:
    """The shaped glyphs of one cluster in a colour font (an emoji), which have no outline to trace.

    Attributes
    ----------
    text : str
        The cluster's characters, for search and copy.
    font : skia.Font
        The colour font at the text's size.
    glyphs : tuple of int
        Glyph ids, usually one for the whole cluster.
    offsets : tuple of (float, float)
        Origin of each glyph relative to the glyph box, in user units.

    Examples
    --------
    >>> from svgwriter._internal._typography._fonts import font_for
    >>> from svgwriter._internal._typography._shaping import ColorGlyphs
    >>> ColorGlyphs("x", font_for("x", "sans-serif", 16), (1,), ((0.0, 0.0),)).glyphs
    (1,)
    """

    text: str
    font: Any
    glyphs: tuple[int, ...]
    offsets: tuple[tuple[float, float], ...]

_HB_FONTS: dict[int, Any] = {}


def harfbuzz() -> Any:
    """The ``uharfbuzz`` module, or None when it is not installed."""
    try:
        import uharfbuzz
    except ImportError:
        return None
    return uharfbuzz


def hb_font(typeface: Any) -> Any:
    """A HarfBuzz font reading *typeface*'s tables through skia (cached; table bytes kept alive)."""
    key = typeface.uniqueID()
    if key not in _HB_FONTS:
        hb = harfbuzz()
        tables: dict[str, bytes] = {}

        def table(face: Any, tag: str, data: Any) -> bytes:
            raw = typeface.copyTableData(int.from_bytes(tag.encode("latin-1"), "big"))
            tables[tag] = bytes(raw) if raw is not None else b""
            return tables[tag]

        face = hb.Face.create_for_tables(table, None)
        _HB_FONTS[key] = (hb.Font(face), face.upem, tables, table)
    return _HB_FONTS[key]


def needs_shaping(text: str) -> bool:
    """Whether *text* needs a shaper: complex scripts (Hebrew, Arabic, Indic, Thai, ...) and emoji sequences.

    Always False without ``uharfbuzz``, so text then lays out glyph by glyph.
    """
    shaped = any(COMPLEX_SCRIPT_START <= ord(char) < LATIN_EXTENDED_ADDITIONAL
                 or CJK_START <= ord(char) < EMOJI_START or EMOJI_START <= ord(char) <= EMOJI_END
                 or char in EMOJI_JOINERS for char in text)
    return shaped and harfbuzz() is not None


def shape_run(text: str, font: Any) -> list[tuple[PathData, float, ColorGlyphs | None]]:
    """Shape *text* with HarfBuzz into one ``(outline, advance, colour glyphs)`` per character.

    The first character of each cluster carries its glyphs, already placed
    relative to the run's start; the last character carries the run's whole
    advance, so per-character layout code places the run as one piece. Glyphs
    of a colour font that have no outline (emoji) are returned as
    :class:`ColorGlyphs` instead, to be drawn as real glyphs.

    Parameters
    ----------
    text : str
        One run in a single font.
    font : skia.Font
        The font that draws the run, at its size.

    Returns
    -------
    list of (PathData, float, ColorGlyphs or None)
        Outline, advance and colour glyphs for each character of *text*.

    Raises
    ------
    ImportError
        If ``uharfbuzz`` (a dependency of svgwriter) is missing from the environment.

    Examples
    --------
    >>> from svgwriter._internal._typography._fonts import font_for
    >>> from svgwriter._internal._typography._shaping import needs_shaping, shape_run
    >>> needs_shaping("plain latin")
    False
    >>> [advance > 0 for _, advance, _ in shape_run("ab", font_for("a", "sans-serif", 16))]
    [False, True]
    """
    from ...ops import from_skia
    from ...pathdata import PathData
    from ...transform import Matrix

    hb = harfbuzz()
    if hb is None:
        raise ImportError("text shaping needs uharfbuzz; pip install uharfbuzz")
    shaper, units, _, _ = hb_font(font.getTypeface())
    colored = color_font(font.getTypeface())
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(shaper, buffer, {})
    scale = font.getSize() / units
    outlines: dict[int, list[PathData]] = {}
    colors: dict[int, list[tuple[int, float, float]]] = {}
    pen = 0.0
    for info, position in zip(buffer.glyph_infos, buffer.glyph_positions, strict=True):
        x, y = pen + position.x_offset * scale, -position.y_offset * scale
        glyph = font.getPath(info.codepoint)
        if glyph is not None and (glyph.countVerbs() or not colored):
            outlines.setdefault(info.cluster, []).append(from_skia(glyph).transformed(Matrix.translate(x, y)))
        elif colored:
            colors.setdefault(info.cluster, []).append((info.codepoint, x, y))
        pen += position.x_advance * scale
    starts = sorted({*outlines, *colors, len(text)})
    result: list[tuple[PathData, float, ColorGlyphs | None]] = []
    for index in range(len(text)):
        parts = outlines.get(index, [])
        shape = sum(parts[1:], parts[0]) if parts else PathData()
        color = None
        cluster = text[index:next((start for start in starts if start > index), len(text))]
        if index in colors and cluster.strip():
            glyphs = colors[index]
            color = ColorGlyphs(cluster, font, tuple(g for g, _, _ in glyphs), tuple((x, y) for _, x, y in glyphs))
        result.append((shape, pen if index == len(text) - 1 else 0.0, color))
    return result
