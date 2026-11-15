"""Text outlines and measurement from installed fonts."""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Final, Literal

import skia

from ..path.data import PathData
from ..transform.matrix import Matrix
from ._skia import from_skia

if TYPE_CHECKING:
    from ..elements.shapes import Path

__all__ = ["Anchor", "FontWeight", "GlyphBox", "layout_glyphs", "text_outline", "text_to_path", "text_width"]

Anchor = Literal["start", "middle", "end"]
FontWeight = int | Literal["normal", "bold"]

DEFAULT_FAMILY: Final = "sans-serif"
DEFAULT_SIZE: Final = 16.0
NORMAL_WEIGHT: Final = 400
BOLD_WEIGHT: Final = 700
NORMAL_WIDTH: Final = 5
GENERIC_FAMILIES: Final = frozenset({"serif", "sans-serif", "monospace", "cursive", "fantasy"})
_ANCHOR_SHIFT: Final = {"start": 0.0, "middle": 0.5, "end": 1.0}


def _weight(value: FontWeight) -> int:
    if value == "normal":
        return NORMAL_WEIGHT
    if value == "bold":
        return BOLD_WEIGHT
    return int(value)


def _font(font_family: str, size: float, weight: FontWeight, italic: bool) -> Any:
    slant = skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant
    families = [name.strip().strip("'\"") for name in font_family.split(",") if name.strip()]
    typeface = None
    for family in families or [DEFAULT_FAMILY]:
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


def text_width(
    text: str,
    font_family: str = DEFAULT_FAMILY,
    size: float = DEFAULT_SIZE,
    *,
    weight: FontWeight = "normal",
    italic: bool = False,
) -> float:
    """Advance width of *text* set in the given font."""
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


@dataclass(frozen=True)
class GlyphBox:
    """One laid-out character: its outline in local glyph space and where it sits."""

    char: str
    outline: PathData
    x: float
    y: float
    angle: float
    advance: float

    def placed(self) -> PathData:
        """The outline rotated by ``angle`` and moved to ``(x, y)``."""
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
    font_family, size, weight, italic
        The font, as in :func:`text_outline`.
    x, y : sequence of float
        Absolute positions for the first characters; later ones follow on.
    dx, dy : sequence of float
        Relative shifts per character (each shift carries to the following ones).
    rotate : sequence of float
        Per-character rotation in degrees; the last value repeats.
    anchor : {"start", "middle", "end"}
        ``text-anchor`` applied to the whole run.

    Returns
    -------
    list of GlyphBox
        One entry per character, whitespace included.
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

    Parameters
    ----------
    text : str
        The characters to outline.
    font_family : str
        Family name or comma-separated fallback list.
    size : float
        Font size in user units.
    x, y : float
        Baseline position of the anchor point.
    anchor : {"start", "middle", "end"}
        Horizontal alignment, as ``text-anchor``.
    weight : int or {"normal", "bold"}
        Font weight.
    italic : bool
        Use the italic style.
    **kwargs
        Attributes for the :class:`~svgwriter.Path`.

    """
    from ..elements.shapes import Path

    data = text_outline(text, font_family, size, x=x, y=y, anchor=anchor, weight=weight, italic=italic)
    return Path(data, **kwargs)
