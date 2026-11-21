"""
Per-character glyph placement following SVG 1.1's positioning rules.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from ..._internal._constants import ANCHOR_SHIFT
from ..._internal._typography._fonts import resolve_font
from ...pathdata.data import PathData
from ...transform.matrix import Matrix
from .._constants import DEFAULT_FAMILY, DEFAULT_FONT_SIZE
from .._skia import from_skia

if TYPE_CHECKING:
    from ..._internal._typography._shaping import ColorGlyphs
    from ..text import Anchor, FontWeight

__all__ = ["GlyphBox", "layout_glyphs"]


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
    color : ColorGlyphs, optional
        Colour glyphs (an emoji) drawn for the cluster this character starts, which have no
        outline. Defaults to None.

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
    color: ColorGlyphs | None = None

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
    size: float = DEFAULT_FONT_SIZE,
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
    font = resolve_font(font_family, size, weight, italic)
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
        shift = ANCHOR_SHIFT[anchor] * (boxes[-1].x + boxes[-1].advance - boxes[0].x)
        boxes = [replace(b, x=b.x - shift) for b in boxes]
    return boxes
