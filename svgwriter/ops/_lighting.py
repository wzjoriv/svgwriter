"""
``feDiffuseLighting`` and ``feSpecularLighting`` as skia lighting image filters.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import skia

from ._constants import LIGHT_SOURCES, SPOT_CUTOFF

if TYPE_CHECKING:
    from ..elements.core import Element
    from ._filter_frame import Frame

__all__ = ["lighting_filter"]


def _color(primitive: Element, linear: bool) -> int:
    """The ``lighting-color`` of *primitive* as a skia colour, in linear light when *linear*."""
    from ..attributes.cascade import computed
    from ..color.color import as_color

    text = str(computed(primitive, "lighting-color", "white", []))
    if text == "currentColor":
        text = str(computed(primitive, "color", "black", []))
    red, green, blue, _ = as_color(text).uint8
    color = skia.Color(red, green, blue)
    return skia.ColorFilters.SRGBToLinearGamma().filterColor(color) if linear else color


def _point(source: Element, names: tuple[str, str, str], frame: Frame) -> skia.Point3:
    """A light coordinate triple in user space (bounding-box fractions when ``primitiveUnits`` asks)."""
    x, y, z = (float(source.get(name, 0)) for name in names)
    if frame.bounding and frame.box is not None:
        box = frame.box
        x, y = box.x + x * box.width, box.y + y * box.height
        z *= math.sqrt((box.width ** 2 + box.height ** 2) / 2)
    return skia.Point3(x, y, z)


def _direction(source: Element) -> skia.Point3:
    azimuth = math.radians(float(source.get("azimuth", 0)))
    elevation = math.radians(float(source.get("elevation", 0)))
    return skia.Point3(math.cos(azimuth) * math.cos(elevation), math.sin(azimuth) * math.cos(elevation),
                       math.sin(elevation))


def lighting_filter(primitive: Element, first: Any, frame: Frame, linear: bool) -> Any:
    """``feDiffuseLighting`` or ``feSpecularLighting`` as a skia image filter reading *first*'s alpha.

    Parameters
    ----------
    primitive : Element
        The lighting primitive, holding one light source.
    first : skia.ImageFilter or None
        Its input (None is the layer being filtered).
    frame : Frame
        The filter's frame; light positions follow ``primitiveUnits``.
    linear : bool
        Colours mix in linear light, so ``lighting-color`` is converted.

    Returns
    -------
    skia.ImageFilter
        The lit surface; *first* unchanged when there is no light source.
    """
    light = next((child for child in primitive if getattr(child, "tag", None) in LIGHT_SOURCES), None)
    if light is None:
        return first
    color = _color(primitive, linear)
    scale = float(primitive.get("surfaceScale", 1))
    diffuse = primitive.tag == "feDiffuseLighting"
    if diffuse:
        shading: tuple[float, ...] = (float(primitive.get("diffuseConstant", 1)),)
    else:
        shading = (float(primitive.get("specularConstant", 1)), float(primitive.get("specularExponent", 1)))
    if light.tag == "feDistantLight":
        make = skia.ImageFilters.DistantLitDiffuse if diffuse else skia.ImageFilters.DistantLitSpecular
        return make(_direction(light), color, scale, *shading, first)
    location = _point(light, ("x", "y", "z"), frame)
    if light.tag == "fePointLight":
        make = skia.ImageFilters.PointLitDiffuse if diffuse else skia.ImageFilters.PointLitSpecular
        return make(location, color, scale, *shading, first)
    target = _point(light, ("pointsAtX", "pointsAtY", "pointsAtZ"), frame)
    cone = light.get("limitingConeAngle")
    cutoff = abs(float(cone)) if cone is not None else SPOT_CUTOFF
    make = skia.ImageFilters.SpotLitDiffuse if diffuse else skia.ImageFilters.SpotLitSpecular
    return make(location, target, float(light.get("specularExponent", 1)), cutoff, color, scale, *shading, first)
