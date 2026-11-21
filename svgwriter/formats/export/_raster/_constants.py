"""
Constants for the raster encoders, animated images and icons.
"""

from __future__ import annotations

import struct
from typing import Final

__all__ = [
    "APNG_DELAY_DENOMINATOR",
    "BITS_PER_PIXEL",
    "BLEND_SOURCE",
    "CHANNEL_MAX",
    "CHUNK_HEADER",
    "CRC_SIZE",
    "DEFAULT_GIF_FPS",
    "DEFAULT_QUALITY",
    "DISPOSE_NONE",
    "ICNS_HEADER",
    "ICNS_SIZES",
    "ICNS_TYPES",
    "ICC_FORMATS",
    "ICO_ENTRY",
    "ICO_HEADER",
    "ICO_MAX",
    "ICO_SIZES",
    "LOSSLESS",
    "MILLISECONDS",
    "PNG_MAGIC",
    "PNG_SIGNATURE",
    "RIFF_HEADER",
    "WEBP_ALPHA_FLAG",
    "WEBP_ANIMATION_FLAG",
    "WEBP_CHUNK_HEADER",
    "WEBP_NO_BLEND",
]

DEFAULT_QUALITY: Final = 90
ICC_FORMATS: Final = ("png", "jpeg")
"""Raster formats whose ``icc=`` option converts the pixels and embeds the profile."""
DEFAULT_GIF_FPS: Final = 12.0
PNG_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"
CHUNK_HEADER: Final = 8
CRC_SIZE: Final = 4
APNG_DELAY_DENOMINATOR: Final = 1000
DISPOSE_NONE: Final = 0
BLEND_SOURCE: Final = 0
RIFF_HEADER: Final = 12
WEBP_CHUNK_HEADER: Final = 8
WEBP_ANIMATION_FLAG: Final = 0x02
WEBP_ALPHA_FLAG: Final = 0x10
WEBP_NO_BLEND: Final = 0x02
MILLISECONDS: Final = 1000
LOSSLESS: Final = 100
CHANNEL_MAX: Final = 255
ICO_SIZES: Final = (16, 24, 32, 48, 64, 128, 256)
ICNS_SIZES: Final = (16, 32, 64, 128, 256, 512, 1024)
ICO_MAX: Final = 256
ICO_HEADER: Final = struct.Struct("<HHH")
ICO_ENTRY: Final = struct.Struct("<BBBBHHII")
ICNS_HEADER: Final = struct.Struct(">4sI")
ICNS_TYPES: Final = {16: (b"icp4",), 32: (b"icp5", b"ic11"), 64: (b"icp6", b"ic12"), 128: (b"ic07",),
                     256: (b"ic08", b"ic13"), 512: (b"ic09", b"ic14"), 1024: (b"ic10",)}
PNG_MAGIC: Final = bytes.fromhex("89504e470d0a1a0a")
BITS_PER_PIXEL: Final = 32
