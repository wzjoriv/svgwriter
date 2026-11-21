"""
Constants of ICC colour management: profile keywords, intents and embedded-profile layouts.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "AUTO_PROFILE",
    "CMYK_SCALE",
    "COLOR_PROFILE",
    "DEFAULT_INTENT",
    "ICC_COLOR_RE",
    "ICC_PAINTS",
    "INTENTS",
    "ICC_EXTRA_HINT",
    "JPEG_APP0",
    "JPEG_APP2",
    "JPEG_ICC_CHUNK",
    "JPEG_ICC_HEADER",
    "JPEG_ICC_PREFIX",
    "JPEG_MARKER",
    "JPEG_SEGMENT_LENGTH",
    "JPEG_SOI",
    "JPEG_START_OF_SCAN",
    "LCMS_HINT",
    "OUTPUT_PROFILES",
    "PNG_COLOR_CHUNKS",
    "PNG_ICC_DEFLATE",
    "PNG_ICC_NAME",
    "PNG_CHUNK_OVERHEAD",
    "PNG_ICC_CHUNK",
    "PNG_IMAGE_DATA",
    "PNG_SIGNATURE",
    "PROFILE_CACHE",
    "SRGB_PROFILE",
    "SPACE_SCALES",
]

COLOR_PROFILE: Final = "color-profile"
AUTO_PROFILE: Final = "auto"
SRGB_PROFILE: Final = "srgb"
ICC_PAINTS: Final = ("fill", "stroke", "stop-color", "flood-color", "lighting-color")
ICC_COLOR_RE: Final = re.compile(r"^(?P<head>url\([^)]*\)\s*)?(?P<color>.*?)\s*icc-color\((?P<args>[^)]*)\)\s*$",
                                 re.IGNORECASE)

DEFAULT_INTENT: Final = "perceptual"
INTENTS: Final = {
    "auto": "perceptual",
    "perceptual": "perceptual",
    "relative-colorimetric": "relative",
    "saturation": "saturation",
    "absolute-colorimetric": "absolute",
}

CMYK_SCALE: Final = 100.0
SPACE_SCALES: Final = {"CMYK": CMYK_SCALE, "CMY": CMYK_SCALE}
PROFILE_CACHE: Final = 64

PNG_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"
PNG_ICC_CHUNK: Final = b"iCCP"
PNG_IMAGE_DATA: Final = b"IDAT"
PNG_CHUNK_OVERHEAD: Final = 12

JPEG_SOI: Final = b"\xff\xd8"
JPEG_MARKER: Final = 0xFF
JPEG_APP0: Final = 0xE0
JPEG_APP2: Final = 0xE2
JPEG_START_OF_SCAN: Final = 0xDA
JPEG_SEGMENT_LENGTH: Final = 2
JPEG_ICC_PREFIX: Final = b"ICC_PROFILE\x00"
JPEG_ICC_HEADER: Final = len(JPEG_ICC_PREFIX) + 2
JPEG_ICC_CHUNK: Final = 0xFFFF - JPEG_SEGMENT_LENGTH - JPEG_ICC_HEADER
"""The most profile bytes one ``APP2`` segment holds."""
PNG_ICC_NAME: Final = b"ICC profile"
PNG_ICC_DEFLATE: Final = bytes(2)
"""The name's terminating zero and compression method 0 (deflate) of an ``iCCP`` chunk."""
PNG_COLOR_CHUNKS: Final = frozenset({b"iCCP", b"sRGB", b"gAMA", b"cHRM"})
"""Colour chunks an embedded profile replaces; PNG allows ``iCCP`` without the others."""

OUTPUT_PROFILES: Final = {"srgb": "sRGB", "display-p3": "Display P3"}
"""The profile keywords exports take, and the LittleCMS built-in profile each names."""
ICC_EXTRA_HINT: Final = ("embedding an ICC profile needs the optional 'color' extra: "
                         "pip install pysvgwriter[color]")

LCMS_HINT: Final = ("ICC colour profiles are not applied: install the optional 'color' extra "
                    "(pip install pysvgwriter[color]) to convert icc-color() and profiled images; "
                    "the sRGB fallback is drawn meanwhile")
