"""
Draw ``<text>`` as real glyphs on a skia canvas, so PDF output keeps selectable, searchable text.

Skia's SVG renderer draws no text, so rasters use glyph outlines. A PDF canvas can hold real text
with an embedded font subset, so text whose paint and effects the PDF can reproduce exactly is kept
as a ``<text>`` leaf and drawn here in z-order, like an image. Characters that need a shaper
(Devanagari, Arabic, ...) or have no glyph in any font are drawn as outlines inside the same text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

import skia

from ..transform.matrix import Matrix

if TYPE_CHECKING:
    from ..color.color import Color
    from ..elements.base import Element
    from ..elements.text import Text

__all__ = ["draw_text", "native_text"]

EFFECTS: Final = ("filter", "mask")
NO_DECORATION: Final = ("", "none")
DEFAULT_SIZE: Final = 16.0
MISSING_GLYPH: Final = 0
POSITION_TOLERANCE: Final = 0.01


def native_text(text: Text) -> bool:
    """Whether *text* can be drawn as real glyphs with the same look as its outlines.

    It can when it and its ancestors carry no filter or mask, and every character is painted with a
    plain colour (no gradient or pattern) and no decoration.

    Parameters
    ----------
    text : Text
        A ``<text>`` element of a render copy (styles resolved).

    Returns
    -------
    bool
        True when :func:`draw_text` reproduces it.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops._native_text import native_text
    >>> native_text(svg.Text("hi", fill="red"))
    True
    >>> native_text(svg.Text("hi", filter="url(#blur)"))
    False
    """
    from ..attributes.cascade import computed

    node: Element | None = text
    while node is not None:
        if any(node.attributes.get(name) is not None for name in EFFECTS):
            return False
        node = node.parent
    for source in {id(e): e for e in [text, *text.iter()]}.values():
        for name in ("fill", "stroke"):
            value = computed(source, name, "black" if name == "fill" else "none", [])
            if "url(" in str(value.svg_value() if hasattr(value, "svg_value") else value):
                return False
        if str(computed(source, "text-decoration", "", [])).strip() not in NO_DECORATION:
            return False
    return True


def draw_text(canvas: skia.Canvas, text: Text, root: Element, view: Matrix) -> None:
    """Paint *text* as glyph runs with its transforms, clips, opacity, fill and stroke.

    Parameters
    ----------
    canvas : skia.Canvas
        Destination canvas.
    text : Text
        A ``<text>`` element accepted by :func:`native_text`.
    root : Element
        The tree being rendered; ancestors up to *root* contribute transforms, clips and opacity.
    view : Matrix
        Maps *root*'s parent coordinates to canvas user units.

    See Also
    --------
    native_text : Which texts can be drawn this way.
    """
    from ..elements._geometry import clip_outline
    from ..elements._transformable import Transformable
    from ._layers import _ancestry, _chain, _skia_matrix
    from ._skia import to_skia

    _, opacity = _ancestry(text, root)
    canvas.save()
    canvas.concat(_skia_matrix(view))
    for node in _chain(text, root):
        if isinstance(node, Transformable):
            canvas.concat(_skia_matrix(node.t))
        clip = clip_outline(node)
        if clip is not None:
            canvas.clipPath(to_skia(clip), doAntiAlias=True)
    pending: list[tuple[Any, Any, skia.RSXform]] = []
    for box in text.layout():
        if not box.char.strip():
            continue
        glyph_font = _glyph_font(box)
        if glyph_font is None:
            _flush(canvas, pending, opacity)
            if len(box.outline):
                fill, stroke = _paints(box.source, opacity)
                for paint in (fill, stroke):
                    if paint is not None:
                        canvas.drawPath(to_skia(box.placed()), paint)
            continue
        if pending and (pending[-1][0].source is not box.source or not _same(pending[-1][1], glyph_font)):
            _flush(canvas, pending, opacity)
        turn = Matrix.rotate(box.angle)
        pending.append((box, glyph_font, skia.RSXform(turn.a, turn.b, box.x, box.y)))
    _flush(canvas, pending, opacity)
    canvas.restore()


def _glyph_font(box: Any) -> Any:
    """The skia font that draws *box* as one glyph, or None when it must be an outline."""
    from ..attributes.cascade import computed
    from ..elements._textlayout import _font_size, _font_weight
    from .text import font_for, needs_shaping

    if needs_shaping(box.char) or box.source is None:
        return None
    family = str(computed(box.source, "font-family", "sans-serif", []))
    size = _font_size(computed(box.source, "font-size", DEFAULT_SIZE, []))
    weight = _font_weight(computed(box.source, "font-weight", "normal", []))
    italic = str(computed(box.source, "font-style", "", [])) in ("italic", "oblique")
    font = font_for(box.char, family, size, weight, italic)
    if font is None or font.textToGlyphs(box.char)[:1] in ([], [MISSING_GLYPH]):
        return None
    return font


def _same(first: Any, second: Any) -> bool:
    a, b = first.getTypeface(), second.getTypeface()
    style_a, style_b = a.fontStyle(), b.fontStyle()
    return (a.getFamilyName() == b.getFamilyName()
            and (style_a.weight(), style_a.width(), style_a.slant()) == (style_b.weight(), style_b.width(), style_b.slant())
            and first.getSize() == second.getSize() and first.isEmbolden() == second.isEmbolden()
            and first.getSkewX() == second.getSkewX())


def _flush(canvas: skia.Canvas, pending: list[tuple[Any, Any, skia.RSXform]], opacity: float) -> None:
    """Draw the collected characters as one text blob and empty *pending*.

    The fill is real text; a stroke is drawn over it from the glyph outlines, so the text is written
    once and copies cleanly.
    """
    from ._skia import to_skia

    if not pending:
        return
    boxes, font = [item[0] for item in pending], pending[0][1]
    fill, stroke = _paints(boxes[0].source, opacity)
    chars = "".join(box.char for box in boxes)
    if fill is not None:
        if _natural(boxes, font):
            # Natural advances: one string, which a PDF writes as a single show operator.
            canvas.drawString(chars, boxes[0].x, boxes[0].y, font, fill)
        else:
            blob = skia.TextBlob.MakeFromRSXform(chars, [item[2] for item in pending], font)
            if blob is not None:
                canvas.drawTextBlob(blob, 0, 0, fill)
    if stroke is not None:
        for box in boxes:
            canvas.drawPath(to_skia(box.placed()), stroke)
    pending.clear()


def _natural(boxes: list[Any], font: Any) -> bool:
    """Whether *boxes* sit on one unrotated baseline, each where the font's own advances put it."""
    if any(box.angle != 0 or box.y != boxes[0].y for box in boxes):
        return False
    widths = font.getWidths(font.textToGlyphs("".join(box.char for box in boxes)))
    if len(widths) != len(boxes):
        return False
    pen = boxes[0].x
    for box, width in zip(boxes, widths, strict=True):
        if abs(box.x - pen) > POSITION_TOLERANCE:
            return False
        pen += width
    return True


def _paints(source: Element, opacity: float) -> tuple[skia.Paint | None, skia.Paint | None]:
    """Fill and stroke paints for *source* (None where it is unpainted)."""
    from ..attributes.cascade import computed
    from ..export._flatten import _number
    from ..export._paints import _paint

    fill_paint = stroke_paint = None
    group = opacity * _number(source, "opacity", 1.0, []) if source.tag != "text" else opacity
    fill = _paint(source, "fill", "black", [])
    if fill is not None:
        fill_paint = _solid(fill, group * _number(source, "fill-opacity", 1.0, []))
    stroke = _paint(source, "stroke", "none", [])
    width = _number(source, "stroke-width", 1.0, [])
    if stroke is not None and width > 0:
        paint = _solid(stroke, group * _number(source, "stroke-opacity", 1.0, []))
        paint.setStyle(skia.Paint.kStroke_Style)
        paint.setStrokeWidth(width)
        join = str(computed(source, "stroke-linejoin", "miter", []))
        paint.setStrokeJoin({"round": skia.Paint.kRound_Join, "bevel": skia.Paint.kBevel_Join}.get(
            join, skia.Paint.kMiter_Join))
        stroke_paint = paint
    return fill_paint, stroke_paint


def _solid(color: Color, alpha: float) -> skia.Paint:
    red, green, blue, own = color.rgba
    paint = skia.Paint(AntiAlias=True)
    paint.setColor4f(skia.Color4f(red, green, blue, own * alpha))
    return paint
