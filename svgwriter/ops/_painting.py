"""
Painting element trees with skia: vector runs through the SVG renderer, images and text drawn in paint order.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import skia

from .._internal._render._rendering import renderable_copy
from ..transform.matrix import IDENTITY, Matrix
from ._canvas import make_surface, paint_svg, read_pixels
from ._layers import concealed, draw_image, hidden, layers

if TYPE_CHECKING:
    from ..attributes.viewbox import ViewBox
    from ..color.color import ColorLike
    from ..elements.core import Element

__all__ = ["paint_tree", "render_tree"]


def render_tree(
    root: Element,
    wrap: Callable[[str], str],
    width: float,
    height: float,
    *,
    view: Matrix = IDENTITY,
    scale: float = 1.0,
    background: ColorLike | None = None,
    viewport: bool = False,
    view_box: ViewBox | None = None,
    snapshot: bool = False,
) -> Any:
    """Render the tree under *root*, drawing embedded ``<image>`` pixels in paint order.

    Parameters
    ----------
    root : Element
        A root ``<svg>`` or any element.
    wrap : callable
        Turns the serialized *root* into a complete SVG document.
    width, height : float
        Canvas size in user units.
    view : Matrix, optional
        Maps *root*'s parent coordinates to canvas user units (the ``viewBox`` mapping).
        Defaults to the identity.
    scale : float, optional
        Pixels per user unit. Defaults to 1.0.
    background : color, optional
        Painted under the drawing. Defaults to None.
    viewport : bool, optional
        *root* is the outermost ``<svg>``: draw it at exactly ``width x height``. Defaults to False.
    view_box : ViewBox, optional
        Replace the root's ``viewBox`` while drawing (used for padding). Defaults to None.
    snapshot : bool, optional
        Return the ``skia.Image`` instead of an array (encoders use it directly). Defaults to False.

    Returns
    -------
    numpy.ndarray or skia.Image
        ``float32`` ``(rows, columns, 4)`` straight RGBA in ``0..1``, or the image when
        *snapshot* is true.

    See Also
    --------
    svgwriter.ops.rasterize : Render a whole document.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.render import render_tree
    >>> doc = svg.Document(4, 2)
    >>> _ = doc.rect(0, 0, 4, 2, fill="red")
    >>> render_tree(doc.root, lambda text: text, 4, 2, viewport=True).shape
    (2, 4, 4)
    """
    surface = make_surface(width, height, scale, background)
    paint_tree(surface.getCanvas(), root, wrap, width, height, view=view, viewport=viewport, view_box=view_box)
    return surface.makeImageSnapshot() if snapshot else read_pixels(surface)


def paint_tree(
    canvas: skia.Canvas,
    root: Element,
    wrap: Callable[[str], str],
    width: float,
    height: float,
    *,
    view: Matrix = IDENTITY,
    viewport: bool = False,
    view_box: ViewBox | None = None,
    native_text: bool = False,
) -> None:
    """Paint the tree under *root* onto any skia canvas (raster, PDF, ...).

    Text becomes outlines (or real glyphs with *native_text*) and embedded images are drawn in
    paint order; colour glyphs (emoji), which have no outlines, are always drawn as real glyphs.
    The other arguments match :func:`render_tree`.

    Parameters
    ----------
    canvas : skia.Canvas
        Destination canvas.
    root : Element
        A root ``<svg>`` or any element.
    wrap : callable
        Turns the serialized *root* into a complete SVG document.
    width, height : float
        Canvas size in user units.
    view : Matrix, optional
        Maps *root*'s parent coordinates to canvas user units. Defaults to the identity.
    viewport : bool, optional
        *root* is the outermost ``<svg>``: draw it at exactly ``width x height``. Defaults to False.
    view_box : ViewBox, optional
        Replace the root's ``viewBox`` while drawing. Defaults to None.
    native_text : bool, optional
        Draw text that a canvas can reproduce exactly (plain colours, no filter or mask) as real
        glyphs, so a PDF canvas keeps it selectable. Defaults to False.

    See Also
    --------
    render_tree : Paint onto a new raster surface and return the pixels.

    Examples
    --------
    >>> import skia
    >>> import svgwriter as svg
    >>> from svgwriter.ops.render import paint_tree
    >>> doc = svg.Document(4, 2)
    >>> _ = doc.rect(0, 0, 4, 2, fill="red")
    >>> surface = skia.Surface(4, 2)
    >>> paint_tree(surface.getCanvas(), doc.root, lambda text: text, 4, 2, viewport=True)
    """
    from ..elements.text import Text
    from ..io.writer import to_string
    from ._filters._filtered import draw_filtered, needs_engine
    from ._native_text import draw_text
    from ._native_text import native_text as drawable

    root = renderable_copy(root, keep_text=drawable if native_text else None, color_glyphs=True)
    if viewport:
        root.attributes["width"], root.attributes["height"] = width, height
    if view_box is not None:
        root.attributes["viewBox"] = view_box
    parts = layers(root, needs_engine)
    for run, item in parts:
        if run or len(parts) == 1:
            with concealed(hidden(root, run, needs_engine) if len(parts) > 1 else []):
                paint_svg(canvas, wrap(to_string(root, xml_declaration=False, pretty=False)), width, height)
        if item is not None and needs_engine(item):
            draw_filtered(canvas, item, root, wrap, (width, height), view)
        elif isinstance(item, Text):
            draw_text(canvas, item, root, view, only_color=not (native_text and drawable(item)),
                      searchable=native_text)
        elif item is not None:
            draw_image(canvas, item, root, view)
