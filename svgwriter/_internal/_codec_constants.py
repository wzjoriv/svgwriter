"""
Constants of the raster codecs: PNM, GIF, BMP and TIFF layouts and limits.
"""

from __future__ import annotations

import re
from typing import Final

import numpy as np

__all__ = [
    "BMP_BITS_PER_PIXEL",
    "BMP_BI_BITFIELDS",
    "BMP_FILE_HEADER_SIZE",
    "BMP_LCS_SRGB",
    "BMP_MAGIC",
    "BMP_MASKS",
    "BMP_PIXELS_PER_METER",
    "BMP_V4_HEADER_SIZE",
    "GIF_APPLICATION",
    "GIF_APPLICATION_SIZE",
    "GIF_BLOCK_SIZE",
    "GIF_CENTISECONDS",
    "GIF_DISPOSE_BACKGROUND",
    "GIF_EXTENSION",
    "GIF_FLAG_TRANSPARENT",
    "GIF_GRAPHIC_CONTROL",
    "GIF_GRAPHIC_CONTROL_SIZE",
    "GIF_HEADER",
    "GIF_IMAGE_SEPARATOR",
    "GIF_LOOP_BLOCK_SIZE",
    "GIF_MAX_CODES",
    "GIF_MAX_CODE_SIZE",
    "GIF_MAX_COLORS",
    "GIF_MAX_DIMENSION",
    "GIF_MIN_CODE_SIZE",
    "GIF_MIN_PALETTE",
    "GIF_NETSCAPE",
    "GIF_OPAQUE_THRESHOLD",
    "GIF_PALETTE_FLAG",
    "GIF_TRAILER",
    "LUMA",
    "PNM_BINARY_FROM",
    "PNM_BITMAP",
    "PNM_COMMENT",
    "PNM_MAGIC",
    "PNM_WHITESPACE",
    "TIFF_ALPHA_UNASSOCIATED",
    "TIFF_COMPRESSION_DEFLATE",
    "TIFF_ENTRY",
    "TIFF_HEADER",
    "TIFF_INK_CMYK",
    "TIFF_INLINE",
    "TIFF_PHOTOMETRIC",
    "TIFF_PLANAR_CHUNKY",
    "TIFF_RESOLUTION_DENOMINATOR",
    "TIFF_TAGS",
    "TIFF_TYPES",
    "TIFF_UNIT_INCH",
    "UINT16_MAX",
    "WHITE",
]

LUMA: Final = np.array([0.299, 0.587, 0.114], np.float64)
PNM_BINARY_FROM: Final = 4
PNM_BITMAP: Final = (1, 4)
PNM_COMMENT: Final = re.compile(rb"#[^\r\n]*")
PNM_MAGIC: Final = re.compile(rb"P[1-6]")
PNM_WHITESPACE: Final = b" \t\r\n\v\f"
UINT16_MAX: Final = 65535
WHITE: Final = (255, 255, 255)
GIF_APPLICATION: Final = 0xFF
GIF_APPLICATION_SIZE: Final = 11
GIF_BLOCK_SIZE: Final = 255
GIF_CENTISECONDS: Final = 100
GIF_DISPOSE_BACKGROUND: Final = 0x08
GIF_EXTENSION: Final = 0x21
GIF_FLAG_TRANSPARENT: Final = 0x01
GIF_GRAPHIC_CONTROL: Final = 0xF9
GIF_GRAPHIC_CONTROL_SIZE: Final = 4
GIF_HEADER: Final = b"GIF89a"
GIF_IMAGE_SEPARATOR: Final = 0x2C
GIF_LOOP_BLOCK_SIZE: Final = 3
GIF_MAX_CODE_SIZE: Final = 12
GIF_MAX_CODES: Final = 1 << GIF_MAX_CODE_SIZE
GIF_MAX_COLORS: Final = 256
GIF_MAX_DIMENSION: Final = UINT16_MAX
GIF_MIN_CODE_SIZE: Final = 2
GIF_MIN_PALETTE: Final = 2
GIF_NETSCAPE: Final = b"NETSCAPE2.0"
GIF_OPAQUE_THRESHOLD: Final = 128
GIF_PALETTE_FLAG: Final = 0x80
GIF_TRAILER: Final = b"\x3b"
BMP_BI_BITFIELDS: Final = 3
BMP_BITS_PER_PIXEL: Final = 32
BMP_FILE_HEADER_SIZE: Final = 14
BMP_LCS_SRGB: Final = 0x73524742
BMP_MAGIC: Final = b"BM"
BMP_MASKS: Final = (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
BMP_PIXELS_PER_METER: Final = 2835
BMP_V4_HEADER_SIZE: Final = 108

TIFF_HEADER: Final = b"II*" + bytes(1)
"""Little-endian byte order and the TIFF magic number; the first IFD offset follows."""
TIFF_ENTRY: Final = 12
TIFF_INLINE: Final = 4
"""Bytes of value an IFD entry holds itself; longer values go after the IFD."""
TIFF_TYPES: Final = {"short": (3, "H"), "long": (4, "I"), "rational": (5, "I"), "undefined": (7, "B")}
"""Field types by name: the TIFF type code and the ``struct`` format of one component."""
TIFF_TAGS: Final = {
    "width": 256, "height": 257, "bits": 258, "compression": 259, "photometric": 262, "strip_offsets": 273,
    "samples": 277, "rows_per_strip": 278, "strip_bytes": 279, "x_resolution": 282, "y_resolution": 283,
    "planar": 284, "resolution_unit": 296, "ink_set": 332, "extra_samples": 338, "icc": 34675,
}
TIFF_COMPRESSION_DEFLATE: Final = 8
TIFF_PHOTOMETRIC: Final = {"RGB": 2, "CMYK": 5}
TIFF_PLANAR_CHUNKY: Final = 1
TIFF_UNIT_INCH: Final = 2
TIFF_INK_CMYK: Final = 1
TIFF_ALPHA_UNASSOCIATED: Final = 2
TIFF_RESOLUTION_DENOMINATOR: Final = 1000
