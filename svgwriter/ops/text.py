"""
Text outlines and measurement from installed fonts.
"""

from __future__ import annotations

import os
import warnings
from collections.abc import Sequence
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Final, Literal

import skia

from ..pathdata.data import PathData
from ..transform.matrix import Matrix
from ._skia import from_skia

if TYPE_CHECKING:
    from ..elements.shapes import Path

__all__ = [
    "Anchor", "FontWeight", "GlyphBox", "glyph_shape", "layout_glyphs", "register_font", "text_outline", "text_to_path",
    "text_width",
]

Anchor = Literal["start", "middle", "end"]
FontWeight = int | Literal["normal", "bold"]

DEFAULT_FAMILY: Final = "sans-serif"
DEFAULT_SIZE: Final = 16.0
NORMAL_WEIGHT: Final = 400
BOLD_WEIGHT: Final = 700
NORMAL_WIDTH: Final = 5
GENERIC_FAMILIES: Final = frozenset({"serif", "sans-serif", "monospace", "cursive", "fantasy"})
GENERIC_CANDIDATES: Final = {
    "serif": ("Times New Roman", "Georgia", "Times", "Liberation Serif", "DejaVu Serif", "Noto Serif"),
    "monospace": ("Consolas", "Courier New", "Menlo", "Monaco", "Liberation Mono", "DejaVu Sans Mono",
                  "Noto Sans Mono", "Courier"),
    "cursive": ("Comic Sans MS", "Segoe Script", "Apple Chancery", "URW Chancery L"),
    "fantasy": ("Impact", "Papyrus", "Luminari"),
}
_ANCHOR_SHIFT: Final = {"start": 0.0, "middle": 0.5, "end": 1.0}
ANCHOR_SHIFT: Final = _ANCHOR_SHIFT
FONT_CACHE: Final = 64
GLYPH_CACHE: Final = 8192


def _weight(value: FontWeight) -> int:
    if value == "normal":
        return NORMAL_WEIGHT
    if value == "bold":
        return BOLD_WEIGHT
    return int(value)


_REGISTERED: dict[str, list[Any]] = {}


def register_font(source: str | os.PathLike[str] | bytes, family: str | None = None) -> str:
    """Make a TrueType/OpenType font file usable by name in ``font_family``.

    Text layout, measurement, outlines and rendering then use it, without
    installing it on the system. Register each style file (regular, bold,
    italic) of a family; the closest weight and slant is chosen.

    Parameters
    ----------
    source : str, os.PathLike or bytes
        A ``.ttf``/``.otf``/``.ttc`` file or its contents.
    family : str, optional
        Name to register under. Defaults to None, which uses the family name
        stored in the font.

    Returns
    -------
    str
        The family name to use in ``font_family``.

    Raises
    ------
    ValueError
        If the data is not a font skia can read.

    Examples
    --------
    >>> import svgwriter as svg
    >>> # name = svg.register_font("Inter-Regular.ttf")
    >>> # svg.text("Hello", x=0, y=20, font_family=name).to_path()
    """
    if isinstance(source, bytes):
        typeface = skia.Typeface.MakeFromData(skia.Data.MakeWithCopy(source))
    else:
        typeface = skia.Typeface.MakeFromFile(os.fspath(source))
    if typeface is None:
        raise ValueError(f"cannot read a font from {source if not isinstance(source, bytes) else 'the data'!r}")
    name = family or typeface.getFamilyName()
    _REGISTERED.setdefault(name.lower(), []).append(typeface)
    _font.cache_clear()
    font_for.cache_clear()
    glyph_shape.cache_clear()
    return name


def _registered(family: str, weight: int, slant: Any) -> Any:
    """The registered typeface of *family* closest to the requested weight and slant, if any."""
    faces = _REGISTERED.get(family.lower())
    if not faces:
        return None
    return min(faces, key=lambda face: (face.fontStyle().slant() != slant, abs(face.fontStyle().weight() - weight)))


@lru_cache(maxsize=FONT_CACHE)
def _font(font_family: str, size: float, weight: FontWeight, italic: bool) -> Any:
    slant = skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant
    families = [name.strip().strip("'\"") for name in font_family.split(",") if name.strip()]
    for family in families:
        face = _registered(family, _weight(weight), slant)
        if face is not None:
            return skia.Font(face, size)
    typeface = None
    for family in families or [DEFAULT_FAMILY]:
        for concrete in GENERIC_CANDIDATES.get(family.lower(), ()):
            match = skia.Typeface(concrete, skia.FontStyle(_weight(weight), NORMAL_WIDTH, slant))
            if match.getFamilyName().lower() == concrete.lower():
                return skia.Font(match, size)
        candidate = skia.Typeface(family, skia.FontStyle(_weight(weight), NORMAL_WIDTH, slant))
        if family.lower() in GENERIC_FAMILIES or candidate.getFamilyName().lower() == family.lower():
            typeface = candidate
            break
    if typeface is None:
        typeface = skia.Typeface(families[-1], skia.FontStyle(_weight(weight), NORMAL_WIDTH, slant))
        warnings.warn(
            f"font {font_family!r} not found; using {typeface.getFamilyName()!r}",
            stacklevel=3,
        )
    return skia.Font(typeface, size)


COMPLEX_SCRIPT_START: Final = 0x0590
_HB_FONTS: dict[int, Any] = {}


def needs_shaping(text: str) -> bool:
    """Whether *text* has characters from scripts that need a shaper (Hebrew, Arabic, Indic, Thai, ...).

    Always False without ``uharfbuzz``, so text then lays out glyph by glyph.
    """
    complex_script = any(COMPLEX_SCRIPT_START <= ord(char) < LATIN_EXTENDED_ADDITIONAL
                         or CJK_START <= ord(char) < EMOJI_START for char in text)
    return complex_script and _harfbuzz() is not None


LATIN_EXTENDED_ADDITIONAL: Final = 0x1E00
CJK_START: Final = 0xA800
EMOJI_START: Final = 0x1F000


def _harfbuzz() -> Any:
    try:
        import uharfbuzz
    except ImportError:
        return None
    return uharfbuzz


def _hb_font(typeface: Any) -> Any:
    """A HarfBuzz font reading *typeface*'s tables through skia (cached; table bytes kept alive)."""
    key = typeface.uniqueID()
    if key not in _HB_FONTS:
        hb = _harfbuzz()
        tables: dict[str, bytes] = {}

        def table(face: Any, tag: str, data: Any) -> bytes:
            raw = typeface.copyTableData(int.from_bytes(tag.encode("latin-1"), "big"))
            tables[tag] = bytes(raw) if raw is not None else b""
            return tables[tag]

        face = hb.Face.create_for_tables(table, None)
        _HB_FONTS[key] = (hb.Font(face), face.upem, tables, table)
    return _HB_FONTS[key]


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
    >>> from svgwriter.ops.text import needs_shaping
    >>> needs_shaping("plain latin")
    False
    """
    hb = _harfbuzz()
    if hb is None:
        raise ImportError("text shaping needs uharfbuzz; pip install uharfbuzz")
    first = next((char for char in text if not char.isspace()), text[:1])
    font = font_for(first, font_family, size, weight, italic, language)
    shaper, units, _, _ = _hb_font(font.getTypeface())
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


@lru_cache(maxsize=GLYPH_CACHE)
def font_for(char: str, font_family: str, size: float, weight: FontWeight = "normal", italic: bool = False,
             language: str | None = None) -> Any:
    """The font for *char*: the requested family when it has the glyph, else a system font that does.

    Like a browser, layout falls back per character, so Devanagari, Bengali,
    CJK and other scripts render even when the chosen family lacks them.

    Parameters
    ----------
    char : str
        The character (first code point is used).
    font_family : str
        CSS font family list.
    size : float
        Font size in user units.
    weight : {"normal", "bold"} or int, optional
        Font weight. Defaults to "normal".
    italic : bool, optional
        Prefer an italic face. Defaults to False.
    language : str, optional
        BCP 47 language hint (``"zh"``, ``"ja"``, ...) for choosing among fonts
        that cover the character. Defaults to None.

    Returns
    -------
    skia.Font
        A font that can draw *char*, or the requested one when nothing can.

    Examples
    --------
    >>> from svgwriter.ops.text import font_for
    >>> font_for("A", "sans-serif", 16).getSize()
    16.0
    """
    font = _font(font_family, size, weight, italic)
    if not char or font.unicharToGlyph(ord(char[0])):
        return font
    slant = skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant
    style = skia.FontStyle(_weight(weight), NORMAL_WIDTH, slant)
    family = font.getTypeface().getFamilyName()
    hints = [language] if language else []
    fallback = skia.FontMgr().matchFamilyStyleCharacter(family, style, hints, ord(char[0]))
    if fallback is None:
        return font
    return skia.Font(skia.Typeface(fallback.getFamilyName(), style), size)


@lru_cache(maxsize=GLYPH_CACHE)
def glyph_shape(char: str, font_family: str, size: float, weight: FontWeight = "normal",
                italic: bool = False, language: str | None = None) -> tuple[PathData, float]:
    """Outline (origin on the baseline) and advance width of one character; cached.

    Parameters
    ----------
    char : str
        A single character.
    font_family : str
        Family name or comma-separated fallback list.
    size : float
        Font size in user units.
    weight : int or {"normal", "bold"}, optional
        Font weight. Defaults to "normal".
    italic : bool, optional
        Use the italic style. Defaults to False.

    Returns
    -------
    (PathData, float)
        The glyph outline and its advance width.

    See Also
    --------
    layout_glyphs : Lay out a whole string.

    Examples
    --------
    >>> from svgwriter.ops.text import glyph_shape
    >>> outline, advance = glyph_shape("A", "sans-serif", 16)
    >>> advance > 0
    True
    """
    font = font_for(char, font_family, size, weight, italic, language)
    glyphs = font.textToGlyphs(char)
    if not len(glyphs):
        return PathData(), 0.0
    outline = font.getPath(glyphs[0])
    return (from_skia(outline) if outline is not None else PathData()), float(font.getWidths(glyphs)[0])


def text_width(
    text: str,
    font_family: str = DEFAULT_FAMILY,
    size: float = DEFAULT_SIZE,
    *,
    weight: FontWeight = "normal",
    italic: bool = False,
) -> float:
    """Advance width of *text* set in the given font.

    Parameters
    ----------
    text : str
        The characters to measure.
    font_family : str, optional
        Family name or comma-separated fallback list. Defaults to "sans-serif".
    size : float, optional
        Font size in user units. Defaults to 16.0.
    weight : int or {"normal", "bold"}, optional
        Font weight. Defaults to "normal".
    italic : bool, optional
        Use the italic style. Defaults to False.

    Returns
    -------
    float
        Width in user units.

    See Also
    --------
    text_outline : The glyph outlines themselves.

    Examples
    --------
    >>> from svgwriter.ops import text_width
    >>> text_width("Hello") > text_width("Hi") > 0
    True
    """
    return float(_font(font_family, size, weight, italic).measureText(text))


def text_outline(
    text: str,
    font_family: str = DEFAULT_FAMILY,
    size: float = DEFAULT_SIZE,
    *,
    x: float = 0.0,
    y: float = 0.0,
    anchor: Anchor = "start",
    weight: FontWeight = "normal",
    italic: bool = False,
) -> PathData:
    """Glyph outlines of *text* as path data, baseline at ``(x, y)``.

    ``font_family`` may be a CSS-style list (``"Inter, Arial, sans-serif"``);
    the first installed family wins.

    Parameters
    ----------
    text : str
        The characters to outline.
    font_family : str, optional
        Family name or comma-separated fallback list. Defaults to "sans-serif".
    size : float, optional
        Font size in user units. Defaults to 16.0.
    x, y : float, optional
        Baseline position of the anchor point. Defaults to 0.0.
    anchor : {"start", "middle", "end"}, optional
        Horizontal alignment, as ``text-anchor``. Defaults to "start".
    weight : int or {"normal", "bold"}, optional
        Font weight. Defaults to "normal".
    italic : bool, optional
        Use the italic style. Defaults to False.

    Returns
    -------
    PathData
        The combined outline of all glyphs.

    See Also
    --------
    text_to_path : The same outline wrapped in a ``<path>`` element.

    Examples
    --------
    >>> from svgwriter.ops import text_outline
    >>> len(text_outline("Hi", size=24)) > 0
    True
    """
    font = _font(font_family, size, weight, italic)
    glyphs = font.textToGlyphs(text)
    origin_x = x - _ANCHOR_SHIFT[anchor] * font.measureText(text)
    combined = skia.Path()
    for glyph, position in zip(glyphs, font.getPos(glyphs, skia.Point(origin_x, y)), strict=False):
        outline = font.getPath(glyph)
        if outline is not None:
            combined.addPath(outline, position.x(), position.y())
    return from_skia(combined)


@dataclass
class GlyphBox:
    """One laid-out character: its outline in local glyph space and where it sits.

    Attributes
    ----------
    char : str
        The character.
    outline : PathData
        Glyph outline with its origin on the baseline.
    x, y : float
        Position of the glyph origin.
    angle : float
        Rotation in degrees.
    advance : float
        Advance width of the glyph.
    source : object, optional
        The element the character came from, if any. Defaults to None.

    See Also
    --------
    layout_glyphs : Produce glyph boxes for a string.

    Examples
    --------
    >>> from svgwriter.ops.text import layout_glyphs
    >>> box = layout_glyphs("A", x=(5.0,), y=(7.0,))[0]
    >>> (box.char, box.x, box.y)
    ('A', 5.0, 7.0)
    """

    char: str
    outline: PathData
    x: float
    y: float
    angle: float
    advance: float
    source: Any = None

    def placed(self) -> PathData:
        """The outline rotated by ``angle`` and moved to ``(x, y)``.

        Returns
        -------
        PathData
            The glyph outline in text space.

        Examples
        --------
        >>> from svgwriter.ops.text import layout_glyphs
        >>> len(layout_glyphs("A")[0].placed()) > 0
        True
        """
        return self.outline.transformed(Matrix.translate(self.x, self.y) @ Matrix.rotate(self.angle))


def _pick(values: Sequence[float], index: int) -> float | None:
    return values[index] if index < len(values) else None


def layout_glyphs(
    text: str,
    font_family: str = DEFAULT_FAMILY,
    size: float = DEFAULT_SIZE,
    *,
    x: Sequence[float] = (0.0,),
    y: Sequence[float] = (0.0,),
    dx: Sequence[float] = (),
    dy: Sequence[float] = (),
    rotate: Sequence[float] = (),
    anchor: Anchor = "start",
    weight: FontWeight = "normal",
    italic: bool = False,
) -> list[GlyphBox]:
    """Place each character following SVG 1.1's per-character positioning rules.

    Parameters
    ----------
    text : str
        Characters to lay out.
    font_family : str, optional
        Family name or comma-separated fallback list. Defaults to "sans-serif".
    size : float, optional
        Font size in user units. Defaults to 16.0.
    x, y : sequence of float, optional
        Absolute positions for the first characters; later ones follow on. Defaults to ``(0.0,)``.
    dx, dy : sequence of float, optional
        Relative shifts per character (each shift carries to the following ones). Defaults to none.
    rotate : sequence of float, optional
        Per-character rotation in degrees; the last value repeats. Defaults to none.
    anchor : {"start", "middle", "end"}, optional
        ``text-anchor`` applied to the whole run. Defaults to "start".
    weight : int or {"normal", "bold"}, optional
        Font weight. Defaults to "normal".
    italic : bool, optional
        Use the italic style. Defaults to False.

    Returns
    -------
    list of GlyphBox
        One entry per character, whitespace included.

    See Also
    --------
    text_outline : Outline a whole string without per-character control.

    Examples
    --------
    >>> from svgwriter.ops.text import layout_glyphs
    >>> boxes = layout_glyphs("ab", x=(0.0,), y=(10.0,), rotate=(90.0,))
    >>> [(b.char, b.angle) for b in boxes]
    [('a', 90.0), ('b', 90.0)]
    """
    font = _font(font_family, size, weight, italic)
    glyphs = font.textToGlyphs(text)
    advances = font.getWidths(glyphs)
    pen_x, pen_y = (x[0] if x else 0.0), (y[0] if y else 0.0)
    boxes = []
    for index, (char, glyph, advance) in enumerate(zip(text, glyphs, advances, strict=False)):
        given_x, given_y = _pick(x, index), _pick(y, index)
        pen_x = given_x if given_x is not None else pen_x
        pen_y = given_y if given_y is not None else pen_y
        pen_x += _pick(dx, index) or 0.0
        pen_y += _pick(dy, index) or 0.0
        angle = _pick(rotate, index)
        angle = angle if angle is not None else (rotate[-1] if rotate else 0.0)
        outline = font.getPath(glyph)
        data = from_skia(outline) if outline is not None else PathData()
        boxes.append(GlyphBox(char, data, pen_x, pen_y, angle, float(advance)))
        pen_x += advance
    if boxes and anchor != "start" and len(x) <= 1:
        shift = _ANCHOR_SHIFT[anchor] * (boxes[-1].x + boxes[-1].advance - boxes[0].x)
        boxes = [replace(b, x=b.x - shift) for b in boxes]
    return boxes


def text_to_path(
    text: str,
    font_family: str = DEFAULT_FAMILY,
    size: float = DEFAULT_SIZE,
    *,
    x: float = 0.0,
    y: float = 0.0,
    anchor: Anchor = "start",
    weight: FontWeight = "normal",
    italic: bool = False,
    **kwargs: Any,
) -> Path:
    """A ``<path>`` tracing the glyphs of *text*.

    Useful when the drawing must not depend on fonts being installed where it is viewed.

    Parameters
    ----------
    text : str
        The characters to outline.
    font_family : str, optional
        Family name or comma-separated fallback list. Defaults to "sans-serif".
    size : float, optional
        Font size in user units. Defaults to 16.0.
    x, y : float, optional
        Baseline position of the anchor point. Defaults to 0.0.
    anchor : {"start", "middle", "end"}, optional
        Horizontal alignment, as ``text-anchor``. Defaults to "start".
    weight : int or {"normal", "bold"}, optional
        Font weight. Defaults to "normal".
    italic : bool, optional
        Use the italic style. Defaults to False.
    **kwargs
        Attributes for the :class:`~svgwriter.Path`.

    Returns
    -------
    Path
        The ``<path>`` element.

    See Also
    --------
    text_outline : The outline as bare path data.

    Examples
    --------
    >>> from svgwriter.ops import text_to_path
    >>> text_to_path("Hi", size=24, fill="navy").tag
    'path'
    """
    from ..elements.shapes import Path

    data = text_outline(text, font_family, size, x=x, y=y, anchor=anchor, weight=weight, italic=italic)
    return Path(data, **kwargs)
