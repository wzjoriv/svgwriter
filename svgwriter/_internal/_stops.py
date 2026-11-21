"""
Gradient stops resampled so a renderer that blends in sRGB draws ``color-interpolation: linearRGB`` faithfully.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._constants import (
    LINEAR_RGB,
    LINEAR_STOP_STEPS,
    PERCENT,
    SRGB_GAMMA,
    SRGB_LINEAR_SLOPE,
    SRGB_OFFSET,
    SRGB_THRESHOLD,
)

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["linear_rgb_stops"]


def _to_linear(value: float) -> float:
    if value <= SRGB_THRESHOLD:
        return value / SRGB_LINEAR_SLOPE
    return ((value + SRGB_OFFSET) / (1 + SRGB_OFFSET)) ** SRGB_GAMMA


def _to_srgb(value: float) -> float:
    if value <= SRGB_THRESHOLD / SRGB_LINEAR_SLOPE:
        return value * SRGB_LINEAR_SLOPE
    return (1 + SRGB_OFFSET) * value ** (1 / SRGB_GAMMA) - SRGB_OFFSET


def _offset(stop: Element) -> float:
    text = str(stop.get("offset", 0)).strip()
    value = float(text[:-1]) / PERCENT if text.endswith("%") else float(text)
    return min(max(value, 0.0), 1.0)


def linear_rgb_stops(root: Element) -> None:
    """Resample the stops of every gradient whose ``color-interpolation`` is ``linearRGB``, in place.

    Each pair of stops gets evenly spaced stops in between, blended in linear light, so
    interpolating between them in sRGB draws the linearRGB gradient.

    Parameters
    ----------
    root : Element
        A render copy with self-contained gradients and concrete stop colours.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._stops import linear_rgb_stops
    >>> doc = svg.Document.from_string(
    ...     '<svg xmlns="http://www.w3.org/2000/svg"><linearGradient id="g" color-interpolation="linearRGB">'
    ...     '<stop offset="0" stop-color="black"/><stop offset="1" stop-color="white"/></linearGradient></svg>')
    >>> linear_rgb_stops(doc.root)
    >>> len(list(doc.get_element_by_id("g").iter("stop")))
    17
    """
    from ..attributes.cascade import computed
    from ..color.color import Color, as_color
    from ..elements.paint import Stop

    for gradient in [e for e in root.iter() if e.tag in ("linearGradient", "radialGradient")]:
        if str(computed(gradient, "color-interpolation", "sRGB", [])) != LINEAR_RGB:
            continue
        stops = [child for child in gradient if not isinstance(child, str) and child.tag == "stop"]
        if len(stops) < 2:
            continue
        points = []
        previous = 0.0
        for stop in stops:
            previous = max(previous, _offset(stop))
            color = as_color(str(stop.get("stop-color", "black")))
            points.append((previous, [_to_linear(c) for c in color.rgb], float(stop.get("stop-opacity", 1))))
        for stop in stops:
            gradient.remove(stop)
        for (start, first, alpha), (end, last, omega) in zip(points, points[1:], strict=False):
            for step in range(LINEAR_STOP_STEPS):
                share = step / LINEAR_STOP_STEPS
                mixed = Color(*(_to_srgb(a + (b - a) * share) for a, b in zip(first, last, strict=True)))
                gradient.add(Stop(start + (end - start) * share, mixed.hex, alpha + (omega - alpha) * share))
        end, last, omega = points[-1]
        gradient.add(Stop(end, Color(*(_to_srgb(c) for c in last)).hex, omega))
