"""
Text outlines and measurement from installed fonts.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Literal

import skia

from .._internal._constants import ANCHOR_SHIFT
from .._internal._font_match import FontStyle, describe
from .._internal._font_names import family_names
from .._internal._fonts import font_for, registered_typefaces, resolve_font
from ..pathdata.data import PathData
from ..transform.matrix import Matrix
from ._constants import DEFAULT_FAMILY, DEFAULT_FONT_SIZE, GLYPH_CACHE
from ._glyphs import GlyphBox, layout_glyphs
from ._skia import from_skia

if TYPE_CHECKING:
    from ..elements.shapes import Path

__all__ = [
    "Anchor", "FontWeight", "GlyphBox", "glyph_shape", "layout_glyphs", "register_font", "text_outline", "text_to_path",
    "text_width",
]

Anchor = Literal["start", "middle", "end"]
FontWeight = int | Literal["normal", "bold"]


def register_font(source: str | os.PathLike[str] | bytes, family: str | None = None, *,
                  weight: float | tuple[float, float] | None = None, style: FontStyle | None = None) -> str:
    """Make a TrueType/OpenType font file usable by name in ``font_family``.

    Text layout, measurement, outlines and rendering then use it, without
    installing it on the system. Register each style file (regular, bold,
    italic) of a family; text picks among them with the CSS font matching
    rules, and variable fonts are set to the requested weight. This is the
    low-level call under :class:`~svgwriter.ops.Typeface`, which registers
    a whole family at once.

    Parameters
    ----------
    source : str, os.PathLike or bytes
        A ``.ttf``/``.otf``/``.ttc`` file or its contents.
    family : str, optional
        Name to register under. Defaults to None, which uses the family name
        stored in the font (typographic family first, then WWS, then legacy).
    weight : float or (float, float), optional
        The weight (or variable range) the face stands for, as the
        ``font-weight`` descriptor of ``@font-face``. Defaults to None, which
        reads it from the font (OS/2 weight class or ``wght`` axis).
    style : {"normal", "italic", "oblique"}, optional
        The style the face stands for. Defaults to None, which reads it from the font.

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
    names = family_names(typeface)
    name = family or names[0]
    registered_typefaces.setdefault(name.lower(), []).append(
        (typeface, describe(typeface, weight, style, subfamily=names[1])))
    resolve_font.cache_clear()
    font_for.cache_clear()
    glyph_shape.cache_clear()
    return name


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
    size: float = DEFAULT_FONT_SIZE,
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
    if text.isascii():
        return float(resolve_font(font_family, size, weight, italic).measureText(text))
    boxes = _laid_out(text, font_family, size, weight, italic)
    return float(boxes[-1].x + boxes[-1].advance - boxes[0].x) if boxes else 0.0


def _laid_out(text: str, font_family: str, size: float, weight: FontWeight, italic: bool) -> list[Any]:
    """Glyph boxes from the full text engine (per-character font fallback and shaping included)."""
    from ..elements.text import Text

    element = Text(text, x=0, y=0, font_family=font_family, font_size=size, xml_space="preserve",
                   font_weight=None if weight == "normal" else weight, font_style="italic" if italic else None)
    return element.layout()


def text_outline(
    text: str,
    font_family: str = DEFAULT_FAMILY,
    size: float = DEFAULT_FONT_SIZE,
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
    boxes = _laid_out(text, font_family, size, weight, italic)
    if not boxes:
        return PathData()
    width = boxes[-1].x + boxes[-1].advance - boxes[0].x
    shift = Matrix.translate(x - ANCHOR_SHIFT[anchor] * width, y)
    return sum((box.placed() for box in boxes), PathData()).transformed(shift)


def text_to_path(
    text: str,
    font_family: str = DEFAULT_FAMILY,
    size: float = DEFAULT_FONT_SIZE,
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
