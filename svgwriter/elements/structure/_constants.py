"""
Constants for the structural elements: image hrefs, data URIs and compositing keys.
"""

from __future__ import annotations

from typing import Final

__all__ = ["CHANNEL_MAX", "DATA_URI_PREFIX", "DEFAULT_SCALE", "GEOMETRY_KEYS", "HREF", "MIME_TYPES"]

CHANNEL_MAX: Final = 255.0
DATA_URI_PREFIX: Final = "data:"
HREF: Final = "xlink:href"
MIME_TYPES: Final = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}
GEOMETRY_KEYS: Final = frozenset({"x", "y", "width", "height", "xlink:href", "preserveAspectRatio", "transform", "id"})
DEFAULT_SCALE: Final = 1.0
