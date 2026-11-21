"""
Constants for ``svgwriter.widgets``: control defaults, inference rules, redraw timing and the notebook panel.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "BOUNDS_SAMPLES",
    "CONTROLS_ATTRIBUTE",
    "DEBOUNCE_SECONDS",
    "DEFAULT_COLOR",
    "ERROR_STYLE",
    "EXTRA",
    "GIF_SUFFIX",
    "IMAGE_STYLE",
    "PANEL_SUMMARY",
    "PANEL_WIDTH",
    "RENDER_CACHE",
    "SEGMENTED_MAX",
    "SLIDER_SPAN",
    "SLIDER_STEPS",
    "SWATCH_SIZE",
    "SWEEP_DURATION",
]

EXTRA: Final = "pysvgwriter[widget]"
CONTROLS_ATTRIBUTE: Final = "__svgwriter_controls__"

SLIDER_STEPS: Final = 100
SLIDER_SPAN: Final = 2
SEGMENTED_MAX: Final = 4
DEFAULT_COLOR: Final = "#000000"

DEBOUNCE_SECONDS: Final = 0.08
RENDER_CACHE: Final = 64

SWEEP_DURATION: Final = 2.0
BOUNDS_SAMPLES: Final = 9
GIF_SUFFIX: Final = ".gif"

PANEL_WIDTH: Final = "320px"
PANEL_SUMMARY: Final = "Controls for {names}; they appear while the notebook runs."
SWATCH_SIZE: Final = "28px"
IMAGE_STYLE: Final = "max-width:640px;max-height:640px;overflow:auto"
ERROR_STYLE: Final = "color:#b91c1c;white-space:pre-wrap;font-size:12px;margin:4px 0"
