"""
Constants for the shape elements: the empty point list and regular-polygon defaults.
"""

from __future__ import annotations

from typing import Final

import numpy as np

__all__ = ["DEFAULT_SIDES", "EMPTY_POINTS", "FULL_CIRCLE"]

EMPTY_POINTS: Final = np.zeros((0, 2))
EMPTY_POINTS.flags.writeable = False
DEFAULT_SIDES: Final = 6
FULL_CIRCLE: Final = 360.0
