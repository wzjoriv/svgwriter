"""
Icon-font companions: the CSS that names each icon and a cheatsheet of every glyph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..transform import Matrix
from ._compile import FontInfo, GlyphRecord
from ._constants import (
    CHEAT_CELL,
    CHEAT_COLUMNS,
    CHEAT_GAP,
    CHEAT_GLYPH,
    CHEAT_LABEL,
    CHEAT_LABEL_SIZE,
    CHEAT_MUTED,
    CHEAT_STROKE,
)

if TYPE_CHECKING:
    from ..document import Document

__all__ = ["cheatsheet", "icon_css"]


def icon_css(family: str, font: str, css_format: str, prefix: str, icons: dict[str, str]) -> str:
    r"""``@font-face`` for *font* plus one ``::before`` class per icon.

    Parameters
    ----------
    family : str
        The font family.
    font : str
        The font's URL.
    css_format : str
        The ``format()`` hint.
    prefix : str
        The class prefix.
    icons : dict of str to str
        Icon names and their characters.

    Returns
    -------
    str
        The stylesheet.

    Examples
    --------
    >>> from svgwriter.fonts._sheet import icon_css
    >>> print(icon_css("Icons", "i.woff2", "woff2", "icon", {"x": chr(0xE000)}).splitlines()[-1])
    .icon-x::before { content: "\e000"; }
    """
    lines = [
        "@font-face {",
        f'  font-family: "{family}";',
        f'  src: url("{font}") format("{css_format}");',
        "  font-display: block;",
        "}",
        "",
        f'[class^="{prefix}-"]::before, [class*=" {prefix}-"]::before {{',
        f'  font-family: "{family}";',
        "  font-style: normal;",
        "  font-weight: normal;",
        "  font-variant: normal;",
        "  line-height: 1;",
        "  -webkit-font-smoothing: antialiased;",
        "}",
        "",
    ]
    lines += [f'.{prefix}-{name}::before {{ content: "\\{ord(char):x}"; }}' for name, char in icons.items()]
    return "\n".join(lines) + "\n"


def cheatsheet(info: FontInfo, glyphs: list[GlyphRecord], columns: int | None) -> Document:
    """A grid of glyph outlines labelled with name and code point.

    Parameters
    ----------
    info : FontInfo
        The font's metrics.
    glyphs : list of GlyphRecord
        The glyphs to show.
    columns : int or None
        Cells per row; None picks six.

    Returns
    -------
    Document
        The sheet.

    Examples
    --------
    >>> from svgwriter.fonts._sheet import cheatsheet
    >>> from svgwriter.fonts._compile import FontInfo
    >>> cheatsheet(FontInfo("X", "Regular", 400, 1000, 800, 200, 700, 500, 0, "1"), [], None).root[0].tag
    'rect'
    """
    from ..document import Document

    count = columns or CHEAT_COLUMNS
    rows = max(1, -(-len(glyphs) // count))
    pitch_x, pitch_y = CHEAT_CELL + CHEAT_GAP, CHEAT_CELL + CHEAT_LABEL + CHEAT_GAP
    doc = Document(CHEAT_GAP + min(count, max(len(glyphs), 1)) * pitch_x, CHEAT_GAP + rows * pitch_y)
    doc.rect(0, 0, "100%", "100%", fill="white")
    scale = CHEAT_CELL * CHEAT_GLYPH / info.units_per_em
    for index, glyph in enumerate(glyphs):
        x = CHEAT_GAP + index % count * pitch_x
        y = CHEAT_GAP + index // count * pitch_y
        doc.rect(x, y, CHEAT_CELL, CHEAT_CELL + CHEAT_LABEL, rx=CHEAT_GAP / 2, fill="none", stroke=CHEAT_STROKE)
        baseline = y + CHEAT_CELL / 2 + (info.ascent - info.descent) * scale / 2
        origin = x + (CHEAT_CELL - glyph.advance * scale) / 2
        doc.path(str(glyph.outline @ Matrix(scale, 0, 0, -scale, origin, baseline)), fill="black")
        label = f"U+{glyph.codepoint:04X}" if glyph.codepoint is not None else ""
        middle = x + CHEAT_CELL / 2
        doc.text(glyph.name, x=middle, y=y + CHEAT_CELL, font_size=CHEAT_LABEL_SIZE, text_anchor="middle")
        doc.text(label, x=middle, y=y + CHEAT_CELL + CHEAT_LABEL / 2, font_size=CHEAT_LABEL_SIZE,
                 text_anchor="middle", fill=CHEAT_MUTED)
    return doc
