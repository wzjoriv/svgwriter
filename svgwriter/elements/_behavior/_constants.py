"""
Constants for the shared element behaviour: attributes left out of copies and the default stroke width.
"""

from __future__ import annotations

from typing import Final

__all__ = ["DEFAULT_STROKE_WIDTH", "NOT_COPIED"]

NOT_COPIED: Final = frozenset({"id", "transform", "clip-path"})
DEFAULT_STROKE_WIDTH: Final = 1.0
