"""
Filters and masks for images drawn outside skia's SVG pass, mapped onto skia's own image filters.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import skia

from ._constants import (
    ALPHA_ONLY,
    BLEND,
    CHANNELS,
    COLOR_MIXING,
    COMPOSITE,
    FRAMED,
    LINEAR_RGB,
    LUMA,
    MASK_CANVAS,
    SOURCE_ALPHA,
    SOURCE_GRAPHIC,
)

if TYPE_CHECKING:
    from ..elements.core import Element
    from ._filter_frame import Frame

__all__ = ["image_filter", "paint_mask"]


def _numbers(value: object) -> list[float]:
    return [float(v) for v in str(value).replace(",", " ").split()] if value is not None else []


def _saturate(s: float) -> list[float]:
    r, g, b = LUMA
    return [r + (1 - r) * s, g - g * s, b - b * s, 0, 0,
            r - r * s, g + (1 - g) * s, b - b * s, 0, 0,
            r - r * s, g - g * s, b + (1 - b) * s, 0, 0,
            0, 0, 0, 1, 0]


def _hue_rotate(degrees: float) -> list[float]:
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return [0.213 + c * 0.787 - s * 0.213, 0.715 - c * 0.715 - s * 0.715, 0.072 - c * 0.072 + s * 0.928, 0, 0,
            0.213 - c * 0.213 + s * 0.143, 0.715 + c * 0.285 + s * 0.140, 0.072 - c * 0.072 - s * 0.283, 0, 0,
            0.213 - c * 0.213 - s * 0.787, 0.715 - c * 0.715 + s * 0.715, 0.072 + c * 0.928 + s * 0.072, 0, 0,
            0, 0, 0, 1, 0]


def _color_matrix(primitive: Element) -> list[float] | None:
    kind, values = str(primitive.get("type", "matrix")), _numbers(primitive.get("values"))
    if kind == "saturate":
        return _saturate(values[0] if values else 1.0)
    if kind == "hueRotate":
        return _hue_rotate(values[0] if values else 0.0)
    if kind == "luminanceToAlpha":
        return [0.0] * 15 + [*LUMA, 0.0, 0.0]
    return values if len(values) == 20 else None


def _linear_transfer(primitive: Element) -> list[float] | None:
    """``feComponentTransfer`` with only linear or identity functions as a color matrix."""
    rows = {"feFuncR": 0, "feFuncG": 1, "feFuncB": 2, "feFuncA": 3}
    matrix = [1.0 if i in (0, 6, 12, 18) else 0.0 for i in range(20)]
    for func in primitive:
        row = rows.get(func.tag)
        kind = str(func.get("type", "identity"))
        if row is None or kind == "identity":
            continue
        if kind != "linear":
            return None
        matrix[row * 5 + row] = float(func.get("slope", 1))
        matrix[row * 5 + 4] = float(func.get("intercept", 0))
    return matrix


def _flood(primitive: Element) -> Any:
    from ..color.color import as_color

    color = as_color(primitive.get("flood-color", "black")).with_alpha(float(primitive.get("flood-opacity", 1)))
    red, green, blue, alpha = color.uint8
    return skia.ImageFilters.ColorFilter(skia.ColorFilters.Blend(skia.Color(red, green, blue, alpha),
                                                                 skia.BlendMode.kSrc), None)


Builder = Callable[[Any, Any, Any], Any]


def _primitive(primitive: Element, first: Any, second: Any) -> Any:
    """One ``fe*`` element as a skia image filter reading *first* (and *second*); unsupported ones pass through."""
    tag = primitive.tag
    if tag == "feGaussianBlur":
        sx, *rest = _numbers(primitive.get("stdDeviation", 0)) or [0.0]
        return skia.ImageFilters.Blur(sx, rest[0] if rest else sx, skia.TileMode.kDecal, first)
    if tag == "feOffset":
        return skia.ImageFilters.Offset(float(primitive.get("dx", 0)), float(primitive.get("dy", 0)), first)
    if tag in ("feColorMatrix", "feComponentTransfer"):
        matrix = _color_matrix(primitive) if tag == "feColorMatrix" else _linear_transfer(primitive)
        return skia.ImageFilters.ColorFilter(skia.ColorFilters.Matrix(matrix), first) if matrix else first
    if tag == "feFlood":
        return _flood(primitive)
    if tag == "feMorphology":
        rx, *rest = _numbers(primitive.get("radius", 0)) or [0.0]
        make = skia.ImageFilters.Dilate if str(primitive.get("operator", "erode")) == "dilate" else skia.ImageFilters.Erode
        return make(rx, rest[0] if rest else rx, first)
    if tag == "feBlend":
        return skia.ImageFilters.Xfermode(BLEND.get(str(primitive.get("mode", "normal")), skia.BlendMode.kSrcOver),
                                          second, first)
    if tag == "feComposite":
        operator = str(primitive.get("operator", "over"))
        if operator == "arithmetic":
            k = [float(primitive.get(name, 0)) for name in ("k1", "k2", "k3", "k4")]
            source = skia.ImageFilters.Offset(0.0, 0.0, None)
            return skia.ImageFilters.Arithmetic(*k, True, second or source, first or source)
        return skia.ImageFilters.Xfermode(COMPOSITE.get(operator, skia.BlendMode.kSrcOver), second, first)
    if tag == "feMerge":
        layers = [node.get("in") for node in primitive if node.tag == "feMergeNode"]
        return ("merge", layers)
    return first


def _linear(made: Any) -> Any:
    return skia.ImageFilters.ColorFilter(skia.ColorFilters.SRGBToLinearGamma(), made)


def _gamma(made: Any) -> Any:
    return skia.ImageFilters.ColorFilter(skia.ColorFilters.LinearToSRGBGamma(), made)


def _framed(primitive: Element, first: Any, second: Any, frame: Frame, area: Any, source_area: Any) -> Any:
    """The primitives only a framed (user-space) filter can build: images, tiles and displacement."""
    from ._filter_frame import image_source

    tag = primitive.tag
    if tag == "feImage":
        return image_source(primitive, area, frame)
    if tag == "feTile":
        return skia.ImageFilters.Tile(source_area, area, first)
    channels = [CHANNELS.get(str(primitive.get(name, "A")), skia.ColorChannel.kA)
                for name in ("xChannelSelector", "yChannelSelector")]
    return skia.ImageFilters.DisplacementMap(*channels, float(primitive.get("scale", 0)), second, first)


def image_filter(filter_element: Element, frame: Frame | None = None) -> Any:
    """The ``<filter>`` as one skia image filter; None when it has no primitives.

    Parameters
    ----------
    filter_element : Element
        The ``<filter>``.
    frame : Frame, optional
        The filter's geometry in the filtered element's user space. With it, primitive
        subregions crop each result, colours mix in ``color-interpolation-filters`` space, and
        ``feImage``, ``feTile`` and ``feDisplacementMap`` are drawn. Defaults to None.

    Returns
    -------
    skia.ImageFilter or None
        The filter graph; the layer drawn with it is ``SourceGraphic``.
    """
    from ..attributes.cascade import computed
    from ..elements.filters.base import FilterPrimitive

    results: dict[str, Any] = {SOURCE_GRAPHIC: None}
    results[SOURCE_ALPHA] = skia.ImageFilters.ColorFilter(skia.ColorFilters.Matrix(ALPHA_ONLY), None)
    regions: dict[str, Any] = {}
    previous: Any = None
    previous_area = frame.region if frame is not None else None
    built = False
    for primitive in filter_element:
        if not isinstance(primitive, FilterPrimitive):
            continue

        def resolve(name: object, default: Any) -> Any:
            return default if name is None else results.get(str(name), default)

        first = resolve(primitive.get("in"), previous)
        second = resolve(primitive.get("in2"), None)
        linear = frame is not None and primitive.tag in COLOR_MIXING and str(
            computed(primitive, "color-interpolation-filters", LINEAR_RGB, [])) == LINEAR_RGB
        if linear:
            first, second = _linear(first), _linear(second) if second is not None else None
        area = source_area = None
        if frame is not None:
            source_area = regions.get(str(primitive.get("in")), frame.region) if primitive.get("in") is not None                 else previous_area
            area = frame.subregion(primitive, frame.region)
        if frame is not None and primitive.tag in FRAMED:
            made = _framed(primitive, first, second, frame, area, source_area)
        else:
            made = _primitive(primitive, first, second)
        if isinstance(made, tuple):
            made = skia.ImageFilters.Merge([_linear(resolve(name, previous)) if linear else resolve(name, previous)
                                            for name in made[1]])
        if linear:
            made = _gamma(made)
        if frame is not None:
            made = skia.ImageFilters.Tile(area, area, made)
            previous_area = area
        previous, built = made, True
        if primitive.get("result") is not None:
            results[str(primitive.get("result"))] = made
            regions[str(primitive.get("result"))] = area
    return previous if built else None


def paint_mask(canvas: skia.Canvas, mask: Element, paint_svg: Callable[[skia.Canvas, str, float, float], None]) -> None:
    """Draw *mask*'s content as a luminance layer that keeps only the masked part of what is under it."""
    from ..io.writer import to_string

    body = "".join(to_string(child, xml_declaration=False, pretty=False) for child in mask)
    text = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{MASK_CANVAS}" height="{MASK_CANVAS}">{body}</svg>')
    layer = skia.Paint(BlendMode=skia.BlendMode.kDstIn, ColorFilter=skia.LumaColorFilter.Make())
    canvas.saveLayer(None, layer)
    paint_svg(canvas, text, MASK_CANVAS, MASK_CANVAS)
    canvas.restore()
