"""
Pictures for svgwriter's own value objects (colors, path data, boxes, matrices, pixels) and their notebook display.
"""

from __future__ import annotations

from typing import Any

from ._constants import GHOST, GRID, GRID_STEP, OUTLINE, STROKE, SWATCH

__all__ = ["Drawable", "ascii_markup"]


class Drawable:
    """Mixin: ``__svgwriter__`` builds an element picture; ``_repr_svg_``/``_repr_png_`` show it in notebooks."""

    __slots__ = ()

    def __svgwriter__(self) -> Any:
        raise NotImplementedError

    def _repr_svg_(self) -> str | None:
        return self.__svgwriter__()._repr_svg_()  # type: ignore[no-any-return]

    def _repr_png_(self) -> bytes | None:
        return self.__svgwriter__()._repr_png_()  # type: ignore[no-any-return]


def color_swatch(color: Any) -> Any:
    """A square of the color over a checkerboard, so transparency shows."""
    from ..model.elements.structure import Group

    half = SWATCH / 2
    group = Group()
    group.rect(0, 0, SWATCH, SWATCH, fill="white", stroke=GHOST, stroke_width=STROKE)
    group.rect(0, 0, half, half, fill=GHOST)
    group.rect(half, half, half, half, fill=GHOST)
    group.rect(0, 0, SWATCH, SWATCH, fill=color)
    return group


def path_picture(data: Any) -> Any:
    """The outline drawn with a thin stroke and no fill."""
    from ..model.elements.shapes import Path

    return Path(data, fill="none", stroke=OUTLINE, stroke_width=STROKE)


def box_picture(box: Any) -> Any:
    """The box as a dashed rectangle with its corner marked."""
    from ..model.elements.structure import Group

    group = Group()
    group.rect(box.x, box.y, box.width, box.height, fill="none", stroke=OUTLINE, stroke_width=STROKE,
               stroke_dasharray="3 2")
    group.circle(box.x, box.y, STROKE * 2, fill=OUTLINE)
    return group


def matrix_picture(matrix: Any) -> Any:
    """A unit grid before (light) and after (dark) the transform, with the transformed x axis marked."""
    from ..model.elements.structure import Group

    size = GRID * GRID_STEP
    group = Group()
    for layer, color, transform in (("before", GHOST, None), ("after", OUTLINE, matrix)):
        grid = group.group(stroke=color, stroke_width=STROKE / 2, fill="none", id=None)
        for step in range(GRID + 1):
            grid.line(step * GRID_STEP, 0, step * GRID_STEP, size)
            grid.line(0, step * GRID_STEP, size, step * GRID_STEP)
        if transform is not None:
            grid.matrix = transform
            grid.line(0, 0, size, 0, stroke="crimson", stroke_width=STROKE)
        del layer
    return group


def pixels_picture(pixels: Any) -> Any:
    """The pixels as an ``<image>`` at their size."""
    from ..model.elements.structure import Image

    return Image(pixels.rgba())


def ascii_markup(markup: str) -> str:
    """*markup* with every non-ASCII character as an XML character reference.

    Notebook viewers that mishandle non-ASCII in SVG outputs (GitHub shows ``\xe0...``) still read these.
    """
    return markup.encode("ascii", "xmlcharrefreplace").decode("ascii")
