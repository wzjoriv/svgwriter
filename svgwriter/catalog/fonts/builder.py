"""
``FontBuilder``: turn drawings into an OpenType font, a web font or an icon font.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from ...model.elements import Element
from ._compile import FontInfo, GlyphRecord, compile_font
from ._constants import (
    CSS_FORMATS,
    DEFAULT_ASCENT,
    DEFAULT_CAP_HEIGHT,
    DEFAULT_DESCENT,
    DEFAULT_FAMILY,
    DEFAULT_ICON_PREFIX,
    DEFAULT_STYLE,
    DEFAULT_UNITS_PER_EM,
    DEFAULT_VERSION,
    DEFAULT_WEIGHT,
    DEFAULT_X_HEIGHT,
    PRIVATE_USE_END,
    PRIVATE_USE_START,
)
from ._glyphs import base_records, char_name, font_format, icon_name, place
from ._outline import painted_outline
from ._sheet import cheatsheet, icon_css

if TYPE_CHECKING:
    from ...document import Document
    from ...ops import Typeface

__all__ = ["FontBuilder"]


class FontBuilder:
    """Build a font from drawings: letters from shapes, icons on private-use code points.

    Drawings keep svgwriter's y-down coordinates. A glyph's baseline is the
    drawing's ``y=0`` (move it with ``baseline=``), so letters are drawn
    above the baseline at negative y and descenders below it at positive y;
    one drawing unit is ``scale`` font units. The outline is shifted so its
    left edge sits ``left`` units after the glyph origin.

    Parameters
    ----------
    family : str, optional
        The family name. Defaults to "Untitled".
    style : str, optional
        The style name ("Regular", "Bold", "Italic", ...). Defaults to "Regular".
    weight : int, optional
        The CSS weight, 100 to 900. Defaults to 400.
    units_per_em : int, optional
        Font units per em. Defaults to 1000.
    ascent, descent : int, optional
        Height above and depth below the baseline, in font units. Default to 800 and 200.
    cap_height, x_height : int, optional
        Height of capitals and of lowercase "x". Default to 700 and 500.
    line_gap : int, optional
        Extra space between lines. Defaults to 0.
    scale : float, optional
        Font units per drawing unit for every glyph. Defaults to 1.0.
    version : str, optional
        The font version. Defaults to "1.000".

    See Also
    --------
    svgwriter.Typeface : Use the built font for text.

    Examples
    --------
    >>> import svgwriter as svg
    >>> fb = svg.FontBuilder(family="Blocks")
    >>> fb.glyph("I", svg.rect(0, -700, 120, 700), left=60, right=60)
    >>> fb.advance("I")
    240
    >>> fb.icon("dot", svg.circle(0, 0, 10))
    '\\ue000'
    >>> blocks = fb.typeface()
    >>> round(svg.text("I", font_family=blocks, font_size=1000).to_path().bbox.height)
    700
    """

    def __init__(self, family: str = DEFAULT_FAMILY, style: str = DEFAULT_STYLE, weight: int = DEFAULT_WEIGHT, *,
                 units_per_em: int = DEFAULT_UNITS_PER_EM, ascent: int = DEFAULT_ASCENT,
                 descent: int = DEFAULT_DESCENT, cap_height: int = DEFAULT_CAP_HEIGHT,
                 x_height: int = DEFAULT_X_HEIGHT, line_gap: int = 0, scale: float = 1.0,
                 version: str = DEFAULT_VERSION) -> None:
        self.info = FontInfo(family, style, weight, units_per_em, ascent, descent, cap_height, x_height, line_gap,
                             version)
        self.scale = scale
        self._glyphs: dict[str, GlyphRecord] = {}
        self._icons: dict[str, str] = {}
        self._kerning: dict[tuple[str, str], int] = {}

    def glyph(self, char: str, shape: Element | None = None, *, advance: float | None = None, left: float = 0,
              right: float = 0, baseline: float = 0, scale: float | None = None) -> None:
        """Add (or replace) the glyph for one character.

        Parameters
        ----------
        char : str
            The character the glyph draws.
        shape : Element, optional
            Any shape, text or group; fills and strokes both become outline,
            overlaps merge. Defaults to None, an empty glyph such as a space.
        advance : float, optional
            The advance width in font units. Defaults to None: the outline's
            width plus *left* and *right*.
        left, right : float, optional
            Side bearings in font units. Default to 0.
        baseline : float, optional
            The drawing y that becomes the baseline. Defaults to 0.
        scale : float, optional
            Font units per drawing unit. Defaults to None, the builder's *scale*.

        Raises
        ------
        ValueError
            If *char* is not one character, or an empty glyph has no *advance*.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder(scale=10)
        >>> fb.glyph("l", svg.path("M0 -70 V0", stroke="black", stroke_width=8, fill="none"), left=40, right=40)
        >>> fb.advance("l")
        160
        """
        if len(char) != 1:
            raise ValueError(f"glyph() takes one character, got {char!r}")
        self._add(char_name(char), ord(char), shape, advance, left, right, baseline, scale)

    def icon(self, name: str, shape: Element, *, size: float | None = None) -> str:
        """Add an icon on the next free private-use code point (U+E000 upward, in call order).

        The drawing is scaled to fit the em (ascent plus descent, or *size*)
        and centered in a square advance. Adding a name again replaces its
        drawing and keeps its code point.

        Parameters
        ----------
        name : str
            The icon's name: its glyph name and CSS class suffix.
        shape : Element
            The drawing, in any coordinates.
        size : float, optional
            The icon's box in font units. Defaults to None, ascent plus descent.

        Returns
        -------
        str
            The character that shows the icon.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder()
        >>> hex(ord(fb.icon("home", svg.rect(0, 0, 24, 24))))
        '0xe000'
        """
        glyph_name = icon_name(name)
        codepoint = self._codepoint(glyph_name)
        box = size if size is not None else self.info.ascent + self.info.descent
        bounds = painted_outline(shape).bbox
        extent = max(bounds.width, bounds.height) if bounds else 0
        fit = box / extent if extent else 1.0
        middle = (self.info.ascent - self.info.descent) / 2
        baseline = (bounds.y + bounds.height / 2 if bounds else 0) + middle / fit
        side = (box - (bounds.width if bounds else 0) * fit) / 2
        self._add(glyph_name, codepoint, shape, box, side, side, baseline, fit)
        self._icons[name] = glyph_name
        return chr(codepoint)

    def kern(self, left: str, right: str, value: float) -> None:
        """Adjust the space between two glyphs.

        Parameters
        ----------
        left, right : str
            Characters or icon names, already added.
        value : float
            Font units; negative pulls the pair together.

        Raises
        ------
        KeyError
            If either glyph is missing.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder()
        >>> fb.glyph("A", svg.path("M0 0 L300 -700 L600 0 Z"))
        >>> fb.glyph("V", svg.path("M0 -700 L300 0 L600 -700 Z"))
        >>> fb.kern("A", "V", -80)
        """
        self._kerning[self._name(left), self._name(right)] = round(value)

    def advance(self, glyph: str) -> int:
        """A glyph's advance width in font units.

        Parameters
        ----------
        glyph : str
            A character or icon name.

        Returns
        -------
        int
            The advance.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder()
        >>> fb.glyph(" ", advance=250)
        >>> fb.advance(" ")
        250
        """
        return self._glyphs[self._name(glyph)].advance

    @property
    def icons(self) -> dict[str, str]:
        """Each icon name with the character that shows it, in code point order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder()
        >>> _ = fb.icon("a", svg.rect(0, 0, 1, 1)), fb.icon("b", svg.rect(0, 0, 1, 1))
        >>> list(fb.icons.values())
        ['\\ue000', '\\ue001']
        """
        return {name: chr(self._glyphs[glyph].codepoint or 0) for name, glyph in self._icons.items()}

    def to_bytes(self, file_format: str = "otf") -> bytes:
        """The compiled font.

        Parameters
        ----------
        file_format : {"otf", "ttf", "woff", "woff2"}, optional
            The container, with or without a leading dot. ``otf``, ``woff``
            and ``woff2`` keep the cubic outlines (CFF); ``ttf`` converts them
            to quadratic TrueType curves. Defaults to "otf".

        Returns
        -------
        bytes
            The font file's content.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder()
        >>> fb.glyph("o", svg.circle(250, -250, 250))
        >>> fb.to_bytes(".ttf")[:4]
        b'\\x00\\x01\\x00\\x00'
        """
        return compile_font(self.info, self._records(), self._kerning, font_format(file_format))

    def save(self, path: str | os.PathLike[str]) -> Path:
        """Write the font; the suffix (``.otf``, ``.ttf``, ``.woff``, ``.woff2``) picks the format.

        Parameters
        ----------
        path : str or os.PathLike
            The file to write.

        Returns
        -------
        pathlib.Path
            The written file.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder(family="Hand")
        >>> # fb.save("Hand.otf"); fb.save("Hand.woff2")
        """
        target = Path(path)
        target.write_bytes(self.to_bytes(target.suffix))
        return target

    def typeface(self) -> Typeface:
        """The font as a :class:`~svgwriter.Typeface`, registered so text can use it at once.

        Returns
        -------
        Typeface
            The family, named after *family*.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder(family="Squares")
        >>> fb.glyph("x", svg.rect(0, -500, 500, 500))
        >>> fb.typeface().name
        'Squares'
        """
        from ...ops import Typeface

        return Typeface.from_files(self.to_bytes(), name=self.info.family)

    def css(self, font: str, *, prefix: str = DEFAULT_ICON_PREFIX) -> str:
        """An icon stylesheet: ``@font-face`` for *font* and a ``.prefix-name::before`` class per icon.

        Parameters
        ----------
        font : str
            The font file's URL as the page sees it; its suffix names the format.
        prefix : str, optional
            The class prefix. Defaults to "icon".

        Returns
        -------
        str
            The CSS.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder(family="Icons")
        >>> _ = fb.icon("rocket", svg.rect(0, 0, 24, 24))
        >>> '.icon-rocket::before { content: "\\\\e000"; }' in fb.css("Icons.woff2")
        True
        """
        return icon_css(self.info.family, font, CSS_FORMATS[font_format(font)], prefix, self.icons)

    def save_css(self, path: str | os.PathLike[str], font: str, *, prefix: str = DEFAULT_ICON_PREFIX) -> Path:
        """Write :meth:`css` to *path*.

        Parameters
        ----------
        path : str or os.PathLike
            The stylesheet to write.
        font : str
            The font file's URL relative to the stylesheet.
        prefix : str, optional
            The class prefix. Defaults to "icon".

        Returns
        -------
        pathlib.Path
            The written stylesheet.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder(family="Icons")
        >>> # fb.save("Icons.woff2"); fb.save_css("icons.css", font="Icons.woff2")
        """
        target = Path(path)
        target.write_text(self.css(font, prefix=prefix), encoding="utf-8")
        return target

    def cheatsheet(self, columns: int | None = None) -> Document:
        """A document showing every glyph with its name and code point.

        Parameters
        ----------
        columns : int, optional
            Cells per row. Defaults to None, six.

        Returns
        -------
        Document
            The sheet; glyphs are drawn as paths, so it needs no font.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fb = svg.FontBuilder()
        >>> _ = fb.icon("star", svg.builder.star(0, 0, 10))
        >>> "U+E000" in fb.cheatsheet().to_string()
        True
        """
        shown = [record for record in self._glyphs.values() if record.outline]
        return cheatsheet(self.info, shown, columns)

    def _codepoint(self, glyph_name: str) -> int:
        if glyph_name in self._glyphs:
            return self._glyphs[glyph_name].codepoint or PRIVATE_USE_START
        taken = {record.codepoint for record in self._glyphs.values()}
        return next(code for code in range(PRIVATE_USE_START, PRIVATE_USE_END + 1) if code not in taken)

    def _name(self, glyph: str) -> str:
        name = self._icons.get(glyph) or (char_name(glyph) if len(glyph) == 1 else glyph)
        if name not in self._glyphs:
            raise KeyError(f"no glyph {glyph!r}; add it with glyph() or icon() first")
        return name

    def _add(self, name: str, codepoint: int, shape: Element | None, advance: float | None, left: float,
             right: float, baseline: float, scale: float | None) -> None:
        factor = self.scale if scale is None else scale
        self._glyphs[name] = place(name, codepoint, shape, advance, left, right, baseline, factor)

    def _records(self) -> list[GlyphRecord]:
        return base_records(self.info, set(self._glyphs)) + list(self._glyphs.values())
