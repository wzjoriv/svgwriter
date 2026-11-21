"""
Paint servers, clipping and markers: gradients, stops, patterns, ``clipPath``, ``mask`` and ``marker``.
"""

from __future__ import annotations

from ._clip import ClipPath, Mask
from ._linear import LinearGradient
from ._marker import Marker
from ._pattern import Pattern
from ._radial import RadialGradient
from ._servers import Gradient, Stop

__all__ = [
    "ClipPath",
    "Gradient",
    "LinearGradient",
    "Marker",
    "Mask",
    "Pattern",
    "RadialGradient",
    "Stop",
]
