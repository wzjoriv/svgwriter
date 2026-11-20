"""
Constants for the filter primitives: colour-matrix size and luma weights.
"""

from __future__ import annotations

from typing import Final

__all__ = ["COLOR_MATRIX_SIZE", "LUMA_BLUE", "LUMA_GREEN", "LUMA_RED"]

COLOR_MATRIX_SIZE: Final = 20
LUMA_RED: Final = 0.2126
LUMA_GREEN: Final = 0.7152
LUMA_BLUE: Final = 0.0722
