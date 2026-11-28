"""
Defaults of the ready-made interactions.
"""

from __future__ import annotations

from typing import Final

__all__ = ["HOVER_OPACITY", "HOVER_STROKE_WIDTH", "PRESS_OPACITY", "PRESS_SECONDS"]

HOVER_OPACITY: Final = 0.85
"""Opacity of a button under the pointer."""
PRESS_OPACITY: Final = 0.6
"""Opacity at the bottom of a button's press flash."""
PRESS_SECONDS: Final = 0.15
"""Length of a button's press flash."""
HOVER_STROKE_WIDTH: Final = 3.0
"""Outline width of a highlighted element."""
