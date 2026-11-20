"""
Constants for the structural elements: image hrefs, data URIs, MIME types and channel scale.
"""

from __future__ import annotations

from typing import Final

__all__ = ["CHANNEL_MAX", "DATA_URI_PREFIX", "HREF", "MIME_TYPES"]

CHANNEL_MAX: Final = 255.0
DATA_URI_PREFIX: Final = "data:"
HREF: Final = "xlink:href"
MIME_TYPES: Final = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}
