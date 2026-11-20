"""
Channel and functional-notation parsing behind ``parse_color``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._constants import CHANNEL_MAX, PERCENT_MAX

if TYPE_CHECKING:
    from .color import Color

__all__ = ["color_function"]


def _channel(token: str) -> float:
    from .color import clamp

    if token.endswith("%"):
        return clamp(float(token[:-1]) / PERCENT_MAX, 0.0, 1.0)
    return clamp(float(token) / CHANNEL_MAX, 0.0, 1.0)


def _alpha(token: str) -> float:
    from .color import clamp

    value = float(token[:-1]) / PERCENT_MAX if token.endswith("%") else float(token)
    return clamp(value, 0.0, 1.0)


def color_function(kind: str, body: str, text: str) -> Color:
    """Build a color from an ``rgb[a](...)`` or ``hsl[a](...)`` body."""
    from .color import Color

    if "/" in body:
        main, _, alpha_text = body.partition("/")
        tokens = main.replace(",", " ").split() + [alpha_text.strip()]
    else:
        tokens = body.replace(",", " ").split()
    if len(tokens) not in (3, 4):
        raise ValueError(f"invalid color: {text!r}")
    alpha = _alpha(tokens[3]) if len(tokens) == 4 else 1.0
    if kind.startswith("hsl"):
        hue = float(tokens[0].removesuffix("deg"))
        return Color.from_hsl(hue, _alpha(tokens[1]), _alpha(tokens[2]), alpha)
    if len({t.endswith("%") for t in tokens[:3]}) != 1:
        raise ValueError(f"mixed number and percent channels: {text!r}")
    return Color(*(_channel(t) for t in tokens[:3]), alpha)
