"""
Constants for the shared element behaviour: attributes left out of copies and the default stroke width and the
non-box pivot names.
"""

from __future__ import annotations

from typing import Final

__all__ = ["BASELINE", "DEFAULT_STROKE_WIDTH", "NOT_COPIED", "ORIGIN"]

NOT_COPIED: Final = frozenset({"id", "transform", "clip-path"})
DEFAULT_STROKE_WIDTH: Final = 1.0
ORIGIN: Final = "origin"
"""Pivot name for the local ``(0, 0)``."""
BASELINE: Final = "baseline"
"""Pivot name for the start of a text's first baseline."""
