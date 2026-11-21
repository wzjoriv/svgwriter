"""
Constants for ``svgwriter.tools.widgets``: control defaults, inference rules, redraw timing and the notebook panel.
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
    "IMAGE_RULE",
    "IMAGE_STYLE",
    "GRID_COLUMNS",
    "GRID_GAP",
    "LABEL_WIDTH",
    "PANEL_SUMMARY",
    "READOUT_WIDTH",
    "RENDER_CACHE",
    "SEGMENTED_MAX",
    "SEGMENTED_WRAP",
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
SEGMENTED_WRAP: Final = 6
DEFAULT_COLOR: Final = "#000000"

DEBOUNCE_SECONDS: Final = 0.08
RENDER_CACHE: Final = 64

SWEEP_DURATION: Final = 2.0
BOUNDS_SAMPLES: Final = 9
GIF_SUFFIX: Final = ".gif"

GRID_COLUMNS: Final = "repeat(auto-fill, minmax(300px, 1fr))"
GRID_GAP: Final = "4px 24px"
LABEL_WIDTH: Final = "96px"
READOUT_WIDTH: Final = "64px"
PANEL_SUMMARY: Final = "Controls for {names}; they appear while the notebook runs."
SWATCH_SIZE: Final = "28px"
IMAGE_STYLE: Final = "width:100%;overflow:auto"
IMAGE_RULE: Final = "<style>.svgwriter-drawing svg{max-width:100%;height:auto}</style>"
ERROR_STYLE: Final = "color:#b91c1c;white-space:pre-wrap;font-size:12px;margin:4px 0"
