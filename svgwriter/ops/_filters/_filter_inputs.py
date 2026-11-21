"""
The standard filter inputs beyond the source: ``BackgroundImage``, ``BackgroundAlpha``, ``FillPaint`` and ``StrokePaint``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import skia

from .._constants import (
    ALPHA_ONLY,
    BACKGROUND_ALPHA,
    BACKGROUND_IMAGE,
    ENABLE_BACKGROUND,
    FILL_PAINT,
    NEW_BACKGROUND,
    PAINT_INPUTS,
    STANDARD_INPUTS,
)

if TYPE_CHECKING:
    from ...model.elements.core import Element

__all__ = ["background_layer", "standard_inputs"]


def _used(effects: Element) -> set[str]:
    """The standard input names *effects*' primitives read."""
    names = set()
    for node in effects.iter():
        for attribute in ("in", "in2"):
            value = node.get(attribute)
            if value is not None and str(value) in STANDARD_INPUTS:
                names.add(str(value))
    return names


def background_layer(element: Element, order: list[Element]) -> list[Element] | None:
    """The leaves of *order* that make up *element*'s background, or None without one.

    The background is what the nearest ancestor with ``enable-background="new"`` has painted
    before *element*.

    Parameters
    ----------
    element : Element
        The filtered element.
    order : list of Element
        Every drawable leaf in paint order, *element* among them.

    Returns
    -------
    list of Element or None
        The leaves before *element* inside that ancestor; None when no ancestor starts a background.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._layers import drawable_order
    >>> from svgwriter.ops._filters._filter_inputs import background_layer
    >>> doc = svg.Document(10, 10)
    >>> group = doc.add(svg.group(enable_background="new"))
    >>> first, second = group.add(svg.Rect(0, 0, 1, 1)), group.add(svg.Circle(0, 0, 1))
    >>> [leaf.tag for leaf in background_layer(second, drawable_order(doc.root))]
    ['rect']
    """
    container = element.parent
    while container is not None and not str(container.get(ENABLE_BACKGROUND, "")).startswith(NEW_BACKGROUND):
        container = container.parent
    if container is None:
        return None
    position = next((index for index, leaf in enumerate(order) if leaf is element), len(order))
    layer = []
    for leaf in order[:position]:
        node = leaf.parent
        while node is not None and node is not container:
            node = node.parent
        if node is container:
            layer.append(leaf)
    return layer


def _paint_rect(element: Element, region: skia.Rect, name: str) -> Element:
    """A rectangle over *region* painted with *element*'s computed fill or stroke."""
    from ...model.attributes.cascade import computed
    from ...model.elements.shapes import Rect

    value = computed(element, name, "black" if name == "fill" else "none", [])
    opacity = computed(element, f"{name}-opacity", 1.0, [])
    paint = value.svg_value() if hasattr(value, "svg_value") else str(value)
    return Rect(x=region.left(), y=region.top(), width=region.width(), height=region.height(), fill=paint,
                fill_opacity=opacity, stroke="none")


def standard_inputs(effects: Element, element: Element, region: skia.Rect,
                    element_source: Callable[[Element], skia.Picture],
                    background: Callable[[], skia.Picture]) -> dict[str, Any]:
    """The standard inputs *effects* reads, as skia image filters in *element*'s user space.

    Parameters
    ----------
    effects : Element
        The ``<filter>``.
    element : Element
        The filtered element; its fill and stroke make ``FillPaint`` and ``StrokePaint``.
    region : skia.Rect
        The filter region; every input covers it.
    element_source : callable
        Draws an element as a picture in *element*'s user space.
    background : callable
        Draws *element*'s background as a picture in its user space.

    Returns
    -------
    dict of str to skia.ImageFilter
        One filter per input name the primitives use.
    """
    used = _used(effects)
    inputs: dict[str, Any] = {}
    if used & {BACKGROUND_IMAGE, BACKGROUND_ALPHA}:
        image = skia.ImageFilters.Picture(background(), region)
        inputs[BACKGROUND_IMAGE] = image
        inputs[BACKGROUND_ALPHA] = skia.ImageFilters.ColorFilter(skia.ColorFilters.Matrix(ALPHA_ONLY), image)
    for name in used & PAINT_INPUTS:
        paint = "fill" if name == FILL_PAINT else "stroke"
        inputs[name] = skia.ImageFilters.Picture(element_source(_paint_rect(element, region, paint)), region)
    return inputs
