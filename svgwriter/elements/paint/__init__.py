"""
Paint servers, clipping and markers: gradients, stops, patterns, ``clipPath``, ``mask`` and ``marker``.
"""

from __future__ import annotations

from ._clip import ClipPath, Marker, Mask
from ._servers import Gradient, LinearGradient, Pattern, RadialGradient, Stop

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
