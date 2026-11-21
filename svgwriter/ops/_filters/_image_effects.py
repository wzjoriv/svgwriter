"""
Filter primitives as skia image filters, and masks, for content drawn outside skia's SVG pass.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import skia

from .._constants import (
    BLEND,
    CHANNEL_MAX,
    COMPOSITE,
    CONVOLVE_ORDER,
    COVERAGE_WHITE,
    EDGE_MODES,
    LUMA,
    MASK_CANVAS,
)

if TYPE_CHECKING:
    from ...elements.core import Element

__all__ = ["paint_mask", "primitive_filter"]


def _numbers(value: object) -> list[float]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    return [float(v) for v in str(value).replace(",", " ").split()]


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
    from ...color.color import as_color

    color = as_color(primitive.get("flood-color", "black")).with_alpha(float(primitive.get("flood-opacity", 1)))
    red, green, blue, alpha = color.uint8
    return skia.ImageFilters.ColorFilter(skia.ColorFilters.Blend(skia.Color(red, green, blue, alpha),
                                                                 skia.BlendMode.kSrc), None)


def _convolve(primitive: Element, first: Any) -> Any:
    """``feConvolveMatrix``: the kernel turned 180 degrees (skia correlates), normalised.

    Without ``preserveAlpha`` the bias is scaled by the source alpha, so it lifts only
    what is painted; skia adds a bias uniformly, in 0..255, which serves ``preserveAlpha``.
    """
    order = [int(v) for v in _numbers(primitive.get("order"))] or [CONVOLVE_ORDER]
    columns, rows = order[0], order[-1]
    kernel = _numbers(primitive.get("kernelMatrix"))
    if len(kernel) != columns * rows:
        return first
    divisor = float(primitive.get("divisor", 0) or 0) or sum(kernel) or 1.0
    target = (int(primitive.get("targetX", columns // 2)), int(primitive.get("targetY", rows // 2)))
    mode = EDGE_MODES.get(str(primitive.get("edgeMode", "duplicate")), skia.TileMode.kClamp)
    keep_alpha = str(primitive.get("preserveAlpha", "false")) == "true"
    bias = float(primitive.get("bias", 0))
    convolved = skia.ImageFilters.MatrixConvolution(
        skia.ISize(columns, rows), kernel[::-1], 1.0 / divisor, bias * CHANNEL_MAX if keep_alpha else 0.0,
        skia.IPoint(columns - 1 - target[0], rows - 1 - target[1]), mode, not keep_alpha, first)
    if keep_alpha or not bias:
        return convolved
    coverage = skia.ImageFilters.ColorFilter(skia.ColorFilters.Matrix(COVERAGE_WHITE), first)
    return skia.ImageFilters.Arithmetic(0.0, 1.0, bias, 0.0, True, coverage, convolved)


def primitive_filter(primitive: Element, first: Any, second: Any, scale: tuple[float, float] = (1.0, 1.0)) -> Any:
    """One ``fe*`` element as a skia image filter reading *first* (and *second*).

    Parameters
    ----------
    primitive : Element
        The primitive.
    first, second : skia.ImageFilter or None
        Its ``in`` and ``in2`` inputs (None is the layer being filtered).
    scale : tuple of (float, float), optional
        User units per primitive unit along x and y: the bounding box size when
        ``primitiveUnits`` is ``objectBoundingBox``. Defaults to ``(1.0, 1.0)``.

    Returns
    -------
    skia.ImageFilter or tuple
        The filter, ``("merge", names)`` for ``feMerge``, or *first* for primitives it cannot build.
    """
    tag = primitive.tag
    if tag == "feGaussianBlur":
        sx, *rest = _numbers(primitive.get("stdDeviation", 0)) or [0.0]
        return skia.ImageFilters.Blur(sx * scale[0], (rest[0] if rest else sx) * scale[1], skia.TileMode.kDecal, first)
    if tag == "feOffset":
        return skia.ImageFilters.Offset(float(primitive.get("dx", 0)) * scale[0], float(primitive.get("dy", 0)) * scale[1],
                                        first)
    if tag in ("feColorMatrix", "feComponentTransfer"):
        matrix = _color_matrix(primitive) if tag == "feColorMatrix" else _linear_transfer(primitive)
        return skia.ImageFilters.ColorFilter(skia.ColorFilters.Matrix(matrix), first) if matrix else first
    if tag == "feFlood":
        return _flood(primitive)
    if tag == "feMorphology":
        rx, *rest = _numbers(primitive.get("radius", 0)) or [0.0]
        make = skia.ImageFilters.Dilate if str(primitive.get("operator", "erode")) == "dilate" else skia.ImageFilters.Erode
        return make(rx * scale[0], (rest[0] if rest else rx) * scale[1], first)
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
    if tag == "feConvolveMatrix":
        return _convolve(primitive, first)
    if tag == "feMerge":
        layers = [node.get("in") for node in primitive if node.tag == "feMergeNode"]
        return ("merge", layers)
    return first


def paint_mask(canvas: skia.Canvas, mask: Element, paint_svg: Callable[[skia.Canvas, str, float, float], None]) -> None:
    """Draw *mask*'s content as a luminance layer that keeps only the masked part of what is under it."""
    from ...io.writer import to_string

    body = "".join(to_string(child, xml_declaration=False, pretty=False) for child in mask)
    text = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{MASK_CANVAS}" height="{MASK_CANVAS}">{body}</svg>')
    layer = skia.Paint(BlendMode=skia.BlendMode.kDstIn, ColorFilter=skia.LumaColorFilter.Make())
    canvas.saveLayer(None, layer)
    paint_svg(canvas, text, MASK_CANVAS, MASK_CANVAS)
    canvas.restore()
