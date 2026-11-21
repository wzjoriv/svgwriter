"""
Constants for batches: colormap tables, the matrix layout and the attributes whose values are lists.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "CHANNEL_MAX",
    "COLORMAPS",
    "COLOR_ATTRIBUTES",
    "DEFAULT_DOT_SIZE",
    "EXACT_INTEGER",
    "HALF",
    "IDENTITY_ROW",
    "LIST_VALUED",
    "MATRIX_SIZE",
    "OPACITY_FOR",
    "RGB",
    "RGBA",
]

CHANNEL_MAX: Final = 255
RGB: Final = 3
RGBA: Final = 4
HALF: Final = 0.5
MATRIX_SIZE: Final = 6
IDENTITY_ROW: Final = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
DEFAULT_DOT_SIZE: Final = 2.0
EXACT_INTEGER: Final = 2.0**53
"""Floats below this are written as integers through int64 without loss."""

COLOR_ATTRIBUTES: Final = frozenset({"fill", "stroke", "stop-color", "flood-color", "lighting-color", "color"})
OPACITY_FOR: Final = {"fill": "fill-opacity", "stroke": "stroke-opacity"}
"""Where the alpha of an RGBA colour column goes."""

LIST_VALUED: Final = frozenset({"stroke-dasharray", "points", "values", "keyTimes", "keySplines", "rotate", "dx", "dy",
                                "x", "y", "kernelMatrix", "tableValues", "filterRes"})
"""Attributes whose scalar value is itself a list, so a list there is one value for every item."""

COLORMAPS: Final[dict[str, tuple[str, ...]]] = {
    "viridis": ("#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58",
                "#b5de2b", "#fde725"),
    "plasma": ("#0d0887", "#46039f", "#7201a8", "#9c179e", "#bd3786", "#d8576b", "#ed7953", "#fb9f3a",
               "#fdca26", "#f0f921"),
    "inferno": ("#000004", "#1b0c41", "#4a0c6b", "#781c6d", "#a52c60", "#cf4446", "#ed6925", "#fb9b06",
                "#f7d13d", "#fcffa4"),
    "magma": ("#000004", "#180f3d", "#440f76", "#721f81", "#9e2f7f", "#cd4071", "#f1605d", "#fd9668",
              "#feca8d", "#fcfdbf"),
    "cividis": ("#00224e", "#123570", "#3b496c", "#575d6d", "#707173", "#8a8678", "#a59c74", "#c3b369",
                "#e1cc55", "#fee838"),
    "turbo": ("#30123b", "#4662d7", "#36aaf9", "#1ae4b6", "#72fe5e", "#c8ef34", "#faba39", "#f66b19",
              "#ca2a04", "#7a0403"),
    "grays": ("#000000", "#ffffff"),
}
"""Perceptual colormaps as evenly spaced stops, interpolated linearly in sRGB."""
