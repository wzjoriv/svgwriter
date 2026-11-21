"""
A ``<filter>`` as one skia image filter graph, run in the filtered element's user space.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import skia

from .._constants import (
    ALPHA_ONLY,
    CHANNELS,
    COLOR_MIXING,
    DISPLACEMENT,
    FRAMED,
    LIGHTING,
    LINEAR_RGB,
    SOURCE_ALPHA,
    SOURCE_GRAPHIC,
)
from ._image_effects import primitive_filter
from ._lighting import lighting_filter

if TYPE_CHECKING:
    from ...model.elements.core import Element
    from ._filter_frame import Frame

__all__ = ["image_filter"]


def _linear(made: Any) -> Any:
    return skia.ImageFilters.ColorFilter(skia.ColorFilters.SRGBToLinearGamma(), made)


def _gamma(made: Any) -> Any:
    return skia.ImageFilters.ColorFilter(skia.ColorFilters.LinearToSRGBGamma(), made)


def _framed(primitive: Element, first: Any, second: Any, frame: Frame, area: skia.Rect,
            source_area: skia.Rect) -> Any:
    """The primitives that need the frame: images, tiles and displacement."""
    from ._filter_frame import image_source

    if primitive.tag == "feImage":
        return image_source(primitive, frame.placement(primitive), frame)
    if primitive.tag == "feTile":
        return skia.ImageFilters.Tile(source_area, area, first)
    channels = [CHANNELS.get(str(primitive.get(name, "A")), skia.ColorChannel.kA)
                for name in ("xChannelSelector", "yChannelSelector")]
    return skia.ImageFilters.DisplacementMap(*channels, float(primitive.get("scale", 0)), second, first)


def image_filter(filter_element: Element, frame: Frame) -> Any:
    """The ``<filter>`` as one skia image filter; None when it has no primitives.

    Every result is cropped to its primitive subregion and colours mix in the space
    ``color-interpolation-filters`` names (``linearRGB`` by default); for ``feDisplacementMap``
    that space applies to the map (``in2``) only.

    Parameters
    ----------
    filter_element : Element
        The ``<filter>``.
    frame : Frame
        The filter's geometry in the filtered element's user space.

    Returns
    -------
    skia.ImageFilter or None
        The graph; the layer drawn with it is ``SourceGraphic``.

    See Also
    --------
    svgwriter.ops._filters._filtered.draw_filtered : Paints an element through the graph.
    """
    from ...model.attributes.cascade import computed
    from ...model.elements.filters.base import FilterPrimitive

    results: dict[str, Any] = {SOURCE_GRAPHIC: None,
                               SOURCE_ALPHA: skia.ImageFilters.ColorFilter(skia.ColorFilters.Matrix(ALPHA_ONLY), None)}
    results.update(frame.inputs)
    regions: dict[str, skia.Rect] = {}
    previous: Any = None
    previous_area = frame.region
    built = False
    for primitive in [child for child in filter_element if isinstance(child, FilterPrimitive)]:

        def resolve(name: object, default: Any) -> Any:
            return default if name is None else results.get(str(name), default)

        source = primitive.get("in")
        first, second = resolve(source, previous), resolve(primitive.get("in2"), None)
        space = str(computed(primitive, "color-interpolation-filters", LINEAR_RGB, [])) == LINEAR_RGB
        linear = primitive.tag in COLOR_MIXING and space
        if linear:
            first, second = _linear(first), _linear(second) if second is not None else None
        elif primitive.tag == DISPLACEMENT and space:
            second = _linear(second)
        source_area = previous_area if source is None else regions.get(str(source), frame.region)
        area = frame.subregion(primitive, frame.region)
        if primitive.tag in LIGHTING:
            made = lighting_filter(primitive, first, frame, linear)
        elif primitive.tag in FRAMED:
            made = _framed(primitive, first, second, frame, area, source_area)
        else:
            made = primitive_filter(primitive, first, second, frame.scale)
        if isinstance(made, tuple):
            made = skia.ImageFilters.Merge([_linear(resolve(name, previous)) if linear else resolve(name, previous)
                                            for name in made[1]])
        if linear:
            made = _gamma(made)
        made = skia.ImageFilters.Tile(area, area, made)
        previous, previous_area, built = made, area, True
        if primitive.get("result") is not None:
            results[str(primitive.get("result"))] = made
            regions[str(primitive.get("result"))] = area
    return previous if built else None
