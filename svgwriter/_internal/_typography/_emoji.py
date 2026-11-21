"""
Colour glyphs (emoji): drawing them on a skia canvas and rendering them as images for formats without colour fonts.
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any

import numpy as np
import skia

from .._constants import CHANNEL_MAX, EMOJI_CELL_LEVELS, EMOJI_PIXELS_PER_EM

if TYPE_CHECKING:
    from ...document import Document
    from ...model.elements.structure import Pixels
    from ...model.transform.matrix import Matrix
    from ...ops.text import GlyphBox
    from .._flat._flatten import Item
    from ._shaping import ColorGlyphs

__all__ = ["color_glyph_boxes", "color_glyph_cells", "color_glyph_images", "draw_glyphs", "render_color_glyphs"]


def draw_glyphs(canvas: skia.Canvas, font: Any, glyphs: Sequence[int], offsets: Sequence[tuple[float, float]],
                place: Matrix, paint: skia.Paint) -> None:
    """Draw *glyphs* with their origins at *offsets* mapped by *place*.

    Unrotated runs use plain positions, so a PDF keeps them on one text line.

    Parameters
    ----------
    canvas : skia.Canvas
        Destination canvas.
    font : skia.Font
        The font of the glyphs.
    glyphs : sequence of int
        Glyph ids.
    offsets : sequence of (float, float)
        Origin of each glyph before *place*.
    place : Matrix
        A rotation, uniform scale and translation.
    paint : skia.Paint
        The paint; colour glyphs only take its opacity.

    Examples
    --------
    >>> import skia
    >>> from svgwriter import Matrix
    >>> from svgwriter._internal._typography._emoji import draw_glyphs
    >>> from svgwriter._internal._typography._fonts import font_for
    >>> font = font_for("A", "sans-serif", 16)
    >>> draw_glyphs(skia.Surface(20, 20).getCanvas(), font, font.textToGlyphs("A"), [(2.0, 16.0)], Matrix(),
    ...             skia.Paint())
    """
    builder = skia.TextBlobBuilder()
    if place.b == 0 and place.c == 0 and place.a == place.d == 1:
        builder.allocRunPos(font, list(glyphs), [skia.Point(*place.apply(dx, dy)) for dx, dy in offsets])
    else:
        builder.allocRunRSXform(font, list(glyphs), [skia.RSXform(place.a, place.b, *place.apply(dx, dy))
                                                     for dx, dy in offsets])
    canvas.drawTextBlob(builder.make(), 0, 0, paint)


def render_color_glyphs(color: ColorGlyphs, alpha: float = 1.0,
                        pixels_per_em: float = EMOJI_PIXELS_PER_EM) -> tuple[Pixels, Matrix]:
    """Render one emoji to pixels.

    Parameters
    ----------
    color : ColorGlyphs
        The shaped emoji.
    alpha : float, optional
        Opacity multiplied into the pixels. Defaults to 1.0.
    pixels_per_em : float, optional
        Resolution, in pixels per font size. Defaults to ``EMOJI_PIXELS_PER_EM`` (72).

    Returns
    -------
    (Pixels, Matrix)
        The pixels and the matrix from their grid to the glyph box (origin on the baseline).

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._typography._emoji import render_color_glyphs
    >>> boxes = [b for b in svg.Text("\\U0001f600", x=0, y=0, font_size=20).layout() if b.color]
    >>> all(render_color_glyphs(b.color)[0].rgba().shape[0] > 0 for b in boxes)
    True
    """
    from ...model.elements.structure import Pixels
    from ...model.transform.matrix import Matrix

    bounds = color.font.getBounds(list(color.glyphs))
    left = min(rect.left() + dx for rect, (dx, _) in zip(bounds, color.offsets, strict=True))
    top = min(rect.top() + dy for rect, (_, dy) in zip(bounds, color.offsets, strict=True))
    right = max(rect.right() + dx for rect, (dx, _) in zip(bounds, color.offsets, strict=True))
    bottom = max(rect.bottom() + dy for rect, (_, dy) in zip(bounds, color.offsets, strict=True))
    scale = pixels_per_em / color.font.getSize()
    columns, rows = max(1, math.ceil((right - left) * scale)), max(1, math.ceil((bottom - top) * scale))
    surface = skia.Surface(columns, rows)
    paint = skia.Paint(AntiAlias=True)
    paint.setColor4f(skia.Color4f(0.0, 0.0, 0.0, alpha))
    grid = Matrix.scale(scale) @ Matrix.translate(-left, -top)
    draw_glyphs(surface.getCanvas(), color.font, color.glyphs, color.offsets, grid, paint)
    pixels = surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType,
                                                 alphaType=skia.kUnpremul_AlphaType)
    return Pixels.from_array(pixels.astype(np.float32) / CHANNEL_MAX), grid.inverse()


def color_glyph_boxes(document: Document) -> Iterator[tuple[GlyphBox, Matrix, float]]:
    """Every emoji of the rendered texts of *document*, with its page placement and opacity.

    Parameters
    ----------
    document : Document
        The document.

    Yields
    ------
    (GlyphBox, Matrix, float)
        The glyph box holding the colour glyphs, the matrix from the box's frame (origin on the
        baseline) to the page (``viewBox`` included) and the fill opacity.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._typography._emoji import color_glyph_boxes
    >>> doc = svg.Document(40, 20)
    >>> _ = doc.text("plain", x=0, y=15)
    >>> list(color_glyph_boxes(doc))
    []
    """
    from ...model.attributes.rules import rules_of
    from ...model.elements import Text
    from ...model.transform.matrix import Matrix
    from ...ops.render import page_size
    from .._flat._flatten import _hidden, _number
    from .._flat._paints import _paint
    from .._render._layers import ancestry, drawable_order
    from .._render._rendering import view_matrix

    with document._prepared():
        width, height = page_size(document)
        view = view_matrix(document, width, height)
        root = document.root
        rules = rules_of(root)
        for text in [e for e in drawable_order(root) if isinstance(e, Text)]:
            if text.characters.isascii() or _hidden(text, root):
                continue
            placement, opacity = ancestry(text, root)
            for box in text.layout():
                if box.color is None or _paint(box.source, "fill", "black", rules) is None:
                    continue
                alpha = opacity * _number(box.source, "fill-opacity", 1.0, rules)
                if box.source is not text:
                    alpha *= _number(box.source, "opacity", 1.0, rules)
                yield box, view @ placement @ Matrix.translate(box.x, box.y) @ Matrix.rotate(box.angle), alpha


def color_glyph_images(document: Document, pixels_per_em: float = EMOJI_PIXELS_PER_EM) -> list[tuple[Pixels, Matrix]]:
    """Each emoji of *document* rendered to pixels, with the matrix from their grid to the page.

    Formats that cannot show colour fonts (EPS, TikZ) place these images instead.

    Parameters
    ----------
    document : Document
        The document.
    pixels_per_em : float, optional
        Resolution, in pixels per font size. Defaults to ``EMOJI_PIXELS_PER_EM`` (72).

    Returns
    -------
    list of (Pixels, Matrix)
        Emoji images in paint order with their placement, like ``Scene.images`` from
        :func:`~svgwriter._internal._flat._flatten.flatten`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._typography._emoji import color_glyph_images
    >>> color_glyph_images(svg.Document(10, 10))
    []
    """
    images = []
    for box, page, alpha in color_glyph_boxes(document):
        assert box.color is not None
        pixels, grid = render_color_glyphs(box.color, alpha, pixels_per_em)
        images.append((pixels, page @ grid))
    return images


def color_glyph_cells(document: Document, pixels_per_em: float) -> list[Item]:
    """Each emoji of *document* as filled pixel cells, for vector formats that cannot embed images (TikZ).

    Colours and opacities are rounded to ``EMOJI_CELL_LEVELS`` steps so neighbouring pixels merge:
    each row's runs of one colour become one rectangle, and each colour one path.

    Parameters
    ----------
    document : Document
        The document.
    pixels_per_em : float
        Resolution, in cells per font size.

    Returns
    -------
    list of Item
        Filled paths in page coordinates, in paint order.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._typography._emoji import color_glyph_cells
    >>> color_glyph_cells(svg.Document(10, 10), 24)
    []
    """
    from ...model.color.color import Color
    from ...model.pathdata import PathBuilder
    from .._flat._flatten import Item

    items: list[Item] = []
    step = EMOJI_CELL_LEVELS - 1
    for pixels, matrix in color_glyph_images(document, pixels_per_em):
        levels = np.rint(pixels.rgba() * step).astype(int)
        cells: dict[tuple[int, ...], list[tuple[float, float]]] = {}
        for row, line in enumerate(levels):
            column = 0
            while column < len(line):
                key = tuple(line[column])
                end = column + 1
                while end < len(line) and tuple(line[end]) == key:
                    end += 1
                if key[3]:
                    corners = [(column, row), (end, row), (end, row + 1), (column, row + 1)]
                    cells.setdefault(key, []).extend(tuple(matrix.apply(x, y)) for x, y in corners)
                column = end
        for (red, green, blue, alpha), points in cells.items():
            builder = PathBuilder()
            for index in range(0, len(points), 4):
                builder.move_to(*points[index])
                for point in points[index + 1:index + 4]:
                    builder.line_to(*point)
                builder.close()
            items.append(Item(builder.build(), Color(red / step, green / step, blue / step), alpha / step, False, None, 1.0, 0.0,
                              "butt", "miter", 4.0, ()))
    return items
