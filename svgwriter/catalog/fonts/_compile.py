"""
Compiling glyph records into OpenType binaries with fontTools.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any

from ...model.pathdata import PathData
from ._constants import (
    CUBIC_TO_QUADRATIC_ERROR,
    FONTS_EXTRA,
    FS_ITALIC,
    FS_REGULAR,
    ITALIC_STYLES,
    MAC_ITALIC,
    OS2_VERSION,
    TRUETYPE_FORMATS,
    USE_TYPO_METRICS,
    WEB_FLAVORS,
    WOFF2_EXTRA,
)
from ._outline import draw_contours

__all__ = ["FontInfo", "GlyphRecord", "compile_font"]


@dataclass(frozen=True)
class GlyphRecord:
    """One glyph ready to compile: name, code point, outline in font units (y up) and advance.

    Examples
    --------
    >>> from svgwriter.catalog.fonts._compile import GlyphRecord
    >>> GlyphRecord("A", 65, PathData(), 600).advance
    600
    """

    name: str
    codepoint: int | None
    outline: PathData
    advance: int


@dataclass(frozen=True)
class FontInfo:
    """Naming and vertical metrics shared by every glyph.

    Examples
    --------
    >>> from svgwriter.catalog.fonts._compile import FontInfo
    >>> FontInfo("Hand", "Regular", 400, 1000, 800, 200, 700, 500, 0, "1.000").units_per_em
    1000
    """

    family: str
    style: str
    weight: int
    units_per_em: int
    ascent: int
    descent: int
    cap_height: int
    x_height: int
    line_gap: int
    version: str


def _ps_name(info: FontInfo) -> str:
    return f"{info.family}-{info.style}".replace(" ", "")


def compile_font(info: FontInfo, glyphs: list[GlyphRecord], kerning: dict[tuple[str, str], int],
                 file_format: str) -> bytes:
    """The font file's bytes in *file_format* (``otf``, ``ttf``, ``woff`` or ``woff2``).

    Parameters
    ----------
    info : FontInfo
        Names and metrics.
    glyphs : list of GlyphRecord
        Every glyph, ``.notdef`` first.
    kerning : dict of (str, str) to int
        Pair adjustments by glyph name.
    file_format : str
        The container; ``ttf`` converts cubic curves to quadratic ones.

    Returns
    -------
    bytes
        The compiled font.

    Raises
    ------
    ImportError
        If fontTools (or brotli for ``woff2``) is missing.

    Examples
    --------
    >>> from svgwriter.catalog.fonts._compile import FontInfo, GlyphRecord, compile_font
    >>> info = FontInfo("Hand", "Regular", 400, 1000, 800, 200, 700, 500, 0, "1.000")
    >>> compile_font(info, [GlyphRecord(".notdef", None, PathData(), 500)], {}, "otf")[:4]
    b'OTTO'
    """
    try:
        from fontTools.fontBuilder import FontBuilder
    except ImportError as error:
        raise ImportError(FONTS_EXTRA) from error
    truetype = file_format in TRUETYPE_FORMATS
    builder = FontBuilder(info.units_per_em, isTTF=truetype)
    builder.setupGlyphOrder([glyph.name for glyph in glyphs])
    builder.setupCharacterMap({glyph.codepoint: glyph.name for glyph in glyphs if glyph.codepoint is not None})
    bounds = _setup_truetype(builder, glyphs) if truetype else _setup_cff(builder, info, glyphs)
    builder.setupHorizontalMetrics({glyph.name: (glyph.advance, bounds[glyph.name]) for glyph in glyphs})
    builder.setupHorizontalHeader(ascent=info.ascent, descent=-info.descent, lineGap=info.line_gap)
    builder.setupNameTable({
        "familyName": info.family,
        "styleName": info.style,
        "uniqueFontIdentifier": f"{info.version};{_ps_name(info)}",
        "fullName": f"{info.family} {info.style}",
        "psName": _ps_name(info),
        "version": f"Version {info.version}",
    })
    italic = info.style.lower() in ITALIC_STYLES
    builder.setupOS2(
        version=OS2_VERSION,
        usWeightClass=info.weight, sTypoAscender=info.ascent, sTypoDescender=-info.descent,
        sTypoLineGap=info.line_gap, usWinAscent=info.ascent, usWinDescent=info.descent,
        sCapHeight=info.cap_height, sxHeight=info.x_height,
        fsSelection=USE_TYPO_METRICS | (FS_ITALIC if italic else FS_REGULAR), achVendID="NONE",
    )
    builder.updateHead(macStyle=MAC_ITALIC if italic else 0)
    builder.setupPost(isFixedPitch=0)
    if kerning:
        _setup_kerning(builder, kerning)
    return _serialize(builder.font, file_format)


def _setup_cff(builder: Any, info: FontInfo, glyphs: list[GlyphRecord]) -> dict[str, int]:
    from fontTools.pens.t2CharStringPen import T2CharStringPen

    charstrings, bounds = {}, {}
    for glyph in glyphs:
        pen = T2CharStringPen(glyph.advance, None)
        draw_contours(glyph.outline, pen)
        charstrings[glyph.name] = pen.getCharString()
        box = glyph.outline.bbox
        bounds[glyph.name] = round(box.x) if box else 0
    builder.setupCFF(_ps_name(info), {"FullName": f"{info.family} {info.style}", "FamilyName": info.family},
                     charstrings, {})
    return bounds


def _setup_truetype(builder: Any, glyphs: list[GlyphRecord]) -> dict[str, int]:
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    shapes, bounds = {}, {}
    for glyph in glyphs:
        pen = TTGlyphPen(None)
        draw_contours(glyph.outline, Cu2QuPen(pen, CUBIC_TO_QUADRATIC_ERROR, reverse_direction=True))
        shapes[glyph.name] = pen.glyph()
    builder.setupGlyf(shapes)
    table = builder.font["glyf"]
    for glyph in glyphs:
        outline = table[glyph.name]
        bounds[glyph.name] = outline.xMin if outline.numberOfContours else 0
    return bounds


def _setup_kerning(builder: Any, kerning: dict[tuple[str, str], int]) -> None:
    from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

    rules = "\n".join(f"  pos \\{left} \\{right} {value};" for (left, right), value in kerning.items())
    addOpenTypeFeaturesFromString(builder.font, f"languagesystem DFLT dflt;\nfeature kern {{\n{rules}\n}} kern;\n")


def _serialize(font: Any, file_format: str) -> bytes:
    if file_format in WEB_FLAVORS:
        font.flavor = file_format
    stream = io.BytesIO()
    try:
        font.save(stream)
    except ImportError as error:
        raise ImportError(WOFF2_EXTRA) from error
    return stream.getvalue()
