"""
Glyph records from drawings: names, placement in font units and the glyphs every font needs.
"""

from __future__ import annotations

from ...model.elements import Element
from ...model.pathdata import PathData
from ...model.transform import Matrix
from ._compile import FontInfo, GlyphRecord
from ._constants import FONT_FORMATS, NOTDEF, NOTDEF_INSET, NOTDEF_WIDTH, PRIVATE_USE_END, SPACE, SPACE_WIDTH
from ._outline import painted_outline

__all__ = ["base_records", "char_name", "font_format", "icon_name", "place"]


def font_format(name: str) -> str:
    """The font format a file name or suffix names.

    Parameters
    ----------
    name : str
        ``"Hand.otf"``, ``".ttf"`` or ``"woff2"``.

    Returns
    -------
    str
        One of ``otf``, ``ttf``, ``woff``, ``woff2``.

    Raises
    ------
    ValueError
        For any other suffix.

    Examples
    --------
    >>> from svgwriter.library.fonts._glyphs import font_format
    >>> font_format("Icons.WOFF2")
    'woff2'
    """
    found = name.rpartition(".")[2].lower()
    if found not in FONT_FORMATS:
        raise ValueError(f"unknown font format {name!r}; expected one of {', '.join(FONT_FORMATS)}")
    return found


def char_name(char: str) -> str:
    """The glyph name of a character: ASCII letters as themselves, others ``uniXXXX``.

    Parameters
    ----------
    char : str
        One character.

    Returns
    -------
    str
        The glyph name.

    Examples
    --------
    >>> from svgwriter.library.fonts._glyphs import char_name
    >>> char_name("A"), char_name("1")
    ('A', 'uni0031')
    """
    code = ord(char)
    if char.isascii() and char.isalpha():
        return char
    return f"uni{code:04X}" if code <= PRIVATE_USE_END else f"u{code:05X}"


def icon_name(name: str) -> str:
    """A valid glyph name for an icon name.

    Parameters
    ----------
    name : str
        The icon's name.

    Returns
    -------
    str
        Letters, digits, ``.`` and ``_`` only, not starting with a digit or dot.

    Examples
    --------
    >>> from svgwriter.library.fonts._glyphs import icon_name
    >>> icon_name("arrow-left"), icon_name("3d")
    ('arrow_left', 'icon_3d')
    """
    cleaned = "".join(c if c.isascii() and (c.isalnum() or c in "._") else "_" for c in name)
    if not cleaned or cleaned[0].isdigit() or cleaned[0] == ".":
        cleaned = f"icon_{cleaned}"
    return cleaned


def place(name: str, codepoint: int, shape: Element | None, advance: float | None, left: float, right: float,
          baseline: float, scale: float) -> GlyphRecord:
    """A glyph record: the drawing's painted outline in y-up font units, left edge at *left*.

    Parameters
    ----------
    name : str
        The glyph name.
    codepoint : int
        The character it maps from.
    shape : Element or None
        The drawing; None for an empty glyph.
    advance : float or None
        The advance; None for outline width plus *left* and *right*.
    left, right : float
        Side bearings in font units.
    baseline : float
        The drawing y that becomes the baseline.
    scale : float
        Font units per drawing unit.

    Returns
    -------
    GlyphRecord
        The placed glyph.

    Raises
    ------
    ValueError
        If the glyph is empty and has no *advance*.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.library.fonts._glyphs import place
    >>> place("I", 73, svg.rect(10, -70, 10, 70), None, 5, 5, 0, 10).outline.bbox
    BBox(x=5.0, y=0.0, width=100.0, height=700.0)
    """
    outline = painted_outline(shape) if shape is not None else PathData()
    bounds = outline.bbox
    if bounds is None:
        if advance is None:
            raise ValueError(f"glyph {name!r} has no outline; give it an advance")
        return GlyphRecord(name, codepoint, outline, round(advance))
    outline = outline @ Matrix(scale, 0, 0, -scale, left - bounds.x * scale, baseline * scale)
    return GlyphRecord(name, codepoint, outline, round(bounds.width * scale + left + right if advance is None else advance))


def base_records(info: FontInfo, names: set[str]) -> list[GlyphRecord]:
    """``.notdef`` (a hollow box) and, unless *names* has one, a space.

    Parameters
    ----------
    info : FontInfo
        The font's metrics.
    names : set of str
        The glyph names already drawn.

    Returns
    -------
    list of GlyphRecord
        The glyphs that come first in the font.

    Examples
    --------
    >>> from svgwriter.library.fonts._compile import FontInfo
    >>> from svgwriter.library.fonts._glyphs import base_records
    >>> info = FontInfo("X", "Regular", 400, 1000, 800, 200, 700, 500, 0, "1")
    >>> [record.name for record in base_records(info, set())]
    ['.notdef', 'uni0020']
    """
    em, ascent = info.units_per_em, info.ascent
    inset, width = em * NOTDEF_INSET, round(em * NOTDEF_WIDTH)
    box = PathData(f"M{inset} 0 V{ascent} H{width - inset} V0 Z "
                   f"M{2 * inset} {inset} H{width - 2 * inset} V{ascent - inset} H{2 * inset} Z")
    records = [GlyphRecord(NOTDEF, None, box, width)]
    if char_name(SPACE) not in names:
        records.append(GlyphRecord(char_name(SPACE), ord(SPACE), PathData(), round(em * SPACE_WIDTH)))
    return records
