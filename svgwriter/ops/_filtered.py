"""
Filtered elements drawn around skia's SVG renderer, for filters it cannot run.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import skia

from .._internal._layers import ancestry, viewport_extent
from ._canvas import paint_svg
from ._constants import ENGINE_PRIMITIVES, PICTURE_BOUNDS
from ._layers import concealed, draw_image, hidden, referenced, skia_matrix

if TYPE_CHECKING:
    from ..elements.core import Element
    from ..transform.matrix import Matrix

__all__ = ["draw_filtered", "needs_engine"]


def needs_engine(element: Element) -> bool:
    """Whether *element*'s filter must run outside skia's SVG renderer.

    Parameters
    ----------
    element : Element
        Any element.

    Returns
    -------
    bool
        True for a filtered embedded image, which that renderer cannot draw, and for a filter
        holding ``feImage``, ``feTile`` or ``feConvolveMatrix``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops._filtered import needs_engine
    >>> needs_engine(svg.Rect())
    False
    """
    from ..elements.structure import Image

    effects = referenced(element, "filter") if element.get("filter") is not None else None
    if effects is None:
        return False
    return (isinstance(element, Image) and element.pixels is not None) or any(
        getattr(child, "tag", None) in ENGINE_PRIMITIVES for child in effects)


def _painted(root: Element, wrap: Callable[[str], str], others: list[Element], extra: Element | None = None) -> str:
    """*root* serialized with *others* hidden (and *extra* appended at the top level)."""
    from ..io.writer import to_string

    if extra is not None:
        root.add(extra)
    try:
        with concealed(others):
            return wrap(to_string(root, xml_declaration=False, pretty=False))
    finally:
        if extra is not None:
            root.remove(extra)


def draw_filtered(canvas: skia.Canvas, element: Element, root: Element, wrap: Callable[[str], str],
                  size: tuple[float, float], view: Matrix) -> None:
    """Paint *element* through its filter, run with skia image filters in the element's user space.

    Parameters
    ----------
    canvas : skia.Canvas
        Destination canvas.
    element : Element
        The filtered element (a leaf or a whole group).
    root : Element
        The render copy being painted.
    wrap : callable
        Turns the serialized *root* into a complete SVG document.
    size : tuple of (float, float)
        Canvas size in user units.
    view : Matrix
        Maps *root*'s parent coordinates to canvas user units.

    See Also
    --------
    svgwriter.ops._filter_graph.image_filter : The filter graph.
    """
    from ..elements.structure import Image
    from ._filter_frame import Frame, filter_region
    from ._filter_graph import image_filter

    effects = referenced(element, "filter")
    if effects is None:
        return
    matrix = view @ ancestry(element, root)[0]
    measure = getattr(element, "local_bbox", None)
    try:
        box = measure() if measure is not None else None
    except (TypeError, ValueError):
        box = None
    viewport = viewport_extent(element)
    region = filter_region(effects, box, viewport)
    if region is None:
        return
    width, height = size
    inverse = skia_matrix(view.inverse())

    def element_source(target: Element) -> skia.Picture:
        recorder = skia.PictureRecorder()
        recording = recorder.beginRecording(skia.Rect(-PICTURE_BOUNDS, -PICTURE_BOUNDS, PICTURE_BOUNDS, PICTURE_BOUNDS))
        recording.concat(inverse)
        copy = target.clone()
        copy.attributes.pop("id", None)
        paint_svg(recording, _painted(root, wrap, hidden(root, [], atomic=needs_engine), copy), width, height)
        return recorder.finishRecordingAsPicture()

    bounding = str(effects.get("primitiveUnits", "userSpaceOnUse")) == "objectBoundingBox"
    graph = image_filter(effects, Frame(box, region, viewport, bounding, element_source))
    others = hidden(root, [element], atomic=needs_engine)
    saved = {name: element.attributes.pop(name) for name in ("filter", "opacity") if name in element.attributes}
    try:
        canvas.save()
        canvas.concat(skia_matrix(matrix))
        canvas.clipRect(region, doAntiAlias=True)
        layer = skia.Paint()
        layer.setImageFilter(graph)
        layer.setAlphaf(float(saved.get("opacity", 1.0)))
        canvas.saveLayer(None, layer)
        canvas.concat(skia_matrix(matrix.inverse()))
        if isinstance(element, Image) and element.pixels is not None:
            draw_image(canvas, element, root, view)
        else:
            paint_svg(canvas, _painted(root, wrap, others), width, height)
        canvas.restore()
        canvas.restore()
    finally:
        element.attributes.update(saved)
