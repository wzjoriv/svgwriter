"""
HarfBuzz access for shaping complex scripts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..pathdata.data import PathData
from ..transform.matrix import Matrix
from ._constants import CJK_START, COMPLEX_SCRIPT_START, EMOJI_START, LATIN_EXTENDED_ADDITIONAL
from ._fonts import font_for
from ._skia import from_skia

if TYPE_CHECKING:
    from .text import FontWeight

__all__ = ["harfbuzz", "hb_font", "needs_shaping", "shape_run"]

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
    """Whether *text* has characters from scripts that need a shaper (Hebrew, Arabic, Indic, Thai, ...).

    Always False without ``uharfbuzz``, so text then lays out glyph by glyph.
    """
    complex_script = any(COMPLEX_SCRIPT_START <= ord(char) < LATIN_EXTENDED_ADDITIONAL
                         or CJK_START <= ord(char) < EMOJI_START for char in text)
    return complex_script and harfbuzz() is not None


def shape_run(text: str, font_family: str, size: float, weight: FontWeight = "normal",
              italic: bool = False, language: str | None = None) -> list[tuple[PathData, float]]:
    """Shape *text* with HarfBuzz into one ``(outline, advance)`` per character.

    The first character of each cluster carries its glyphs, already placed
    relative to the run's start; the last character carries the run's whole
    advance, so per-character layout code places the run as one piece.

    Parameters
    ----------
    text : str
        One run in a single font.
    font_family : str
        CSS font family list.
    size : float
        Font size in user units.
    weight : {"normal", "bold"} or int, optional
        Font weight. Defaults to "normal".
    italic : bool, optional
        Use the italic face. Defaults to False.

    Returns
    -------
    list of (PathData, float)
        Outline and advance for each character of *text*.

    Raises
    ------
    ImportError
        If ``uharfbuzz`` (a dependency of svgwriter) is missing from the environment.

    Examples
    --------
    >>> from svgwriter.ops._shaping import needs_shaping
    >>> needs_shaping("plain latin")
    False
    """
    hb = harfbuzz()
    if hb is None:
        raise ImportError("text shaping needs uharfbuzz; pip install uharfbuzz")
    first = next((char for char in text if not char.isspace()), text[:1])
    font = font_for(first, font_family, size, weight, italic, language)
    shaper, units, _, _ = hb_font(font.getTypeface())
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(shaper, buffer, {})
    scale = size / units
    outlines: dict[int, list[PathData]] = {}
    pen = 0.0
    for info, position in zip(buffer.glyph_infos, buffer.glyph_positions, strict=True):
        glyph = font.getPath(info.codepoint)
        if glyph is not None:
            placed = from_skia(glyph).transformed(
                Matrix.translate(pen + position.x_offset * scale, -position.y_offset * scale))
            outlines.setdefault(info.cluster, []).append(placed)
        pen += position.x_advance * scale
    result = []
    for index in range(len(text)):
        parts = outlines.get(index, [])
        shape = sum(parts[1:], parts[0]) if parts else PathData()
        result.append((shape, pen if index == len(text) - 1 else 0.0))
    return result
