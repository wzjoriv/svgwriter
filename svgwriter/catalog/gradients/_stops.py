"""
Stops sampled in OKLCH and the direction of a linear gradient by angle.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from ...model.color.color import Color, ColorLike, as_color
from ...model.elements import LinearGradient, Stop
from ._constants import SAMPLES, SPACE

__all__ = ["linear", "palette_color", "smooth_stops"]


def smooth_stops(colors: Sequence[ColorLike], samples: int = SAMPLES) -> list[Stop]:
    """Even stops through *colors*, with *samples* extra stops per segment mixed in OKLCH.

    Browsers and renderers interpolate gradients in sRGB, which greys out the middle of a blend between
    distant hues; stops sampled in OKLCH keep the blend vivid and perceptually even.
    """
    points = [as_color(color) for color in colors]
    if len(points) == 1:
        return [Stop(0, points[0]), Stop(1, points[0])]
    segments = len(points) - 1
    stops = []
    for index, (start, stop) in enumerate(zip(points, points[1:], strict=False)):
        for step in range(samples + 1):
            weight = step / (samples + 1)
            color = start.mix(stop, weight, space=SPACE) if step else start
            stops.append(Stop(round((index + weight) / segments, 4), color))
    stops.append(Stop(1, points[-1]))
    return stops


def linear(stops: Sequence[Stop], angle: float, **kwargs: Any) -> LinearGradient:
    """A bounding-box linear gradient running at *angle* degrees (0 left to right, 90 top to bottom)."""
    dx, dy = math.cos(math.radians(angle)) / 2, math.sin(math.radians(angle)) / 2
    ends = {"x1": round(0.5 - dx, 4), "y1": round(0.5 - dy, 4), "x2": round(0.5 + dx, 4), "y2": round(0.5 + dy, 4)}
    return LinearGradient(*stops, **{**ends, **kwargs})


def palette_color(color: ColorLike | None, fallback: Color) -> Color:
    """*color*, or *fallback* when it is None."""
    return as_color(color) if color is not None else fallback
