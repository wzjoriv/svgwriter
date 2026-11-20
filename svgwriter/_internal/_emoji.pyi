import skia
from collections.abc import Iterator, Sequence
from typing import Any
from ..document import Document
from ..elements.structure import Pixels
from ..ops.text import GlyphBox
from ..transform.matrix import Matrix
from ._flatten import Item
from ._shaping import ColorGlyphs

__all__ = [
    "color_glyph_boxes",
    "color_glyph_cells",
    "color_glyph_images",
    "draw_glyphs",
    "render_color_glyphs",
]

def draw_glyphs(
    canvas: skia.Canvas,
    font: Any,
    glyphs: Sequence[int],
    offsets: Sequence[tuple[float, float]],
    place: Matrix,
    paint: skia.Paint,
) -> None: ...

def render_color_glyphs(
    color: ColorGlyphs,
    alpha: float = 1.0,
    pixels_per_em: float = 72,
) -> tuple[Pixels, Matrix]: ...

def color_glyph_boxes(document: Document) -> Iterator[tuple[GlyphBox, Matrix, float]]: ...

def color_glyph_images(document: Document, pixels_per_em: float = 72) -> list[tuple[Pixels, Matrix]]: ...

def color_glyph_cells(document: Document, pixels_per_em: float) -> list[Item]: ...
