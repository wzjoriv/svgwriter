"""
Constants of font faces: CSS matching thresholds, OpenType axis tags, widths and file layout.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "AXIS_SLANT",
    "AXIS_WEIGHT",
    "AXIS_WIDTH",
    "CFF_TABLES",
    "CHECKSUM_MAGIC",
    "FONT_FILE_SUFFIXES",
    "FONT_MIME",
    "HEAD_ADJUSTMENT",
    "HEAD_TABLE",
    "MATCH_WEIGHT_HIGH",
    "MATCH_WEIGHT_LOW",
    "NORMAL_STRETCH",
    "SFNT_CFF",
    "SFNT_CHECKSUM_MASK",
    "SFNT_HEADER",
    "SFNT_RECORD",
    "SFNT_TRUETYPE",
    "STANDALONE_SUFFIXES",
    "STYLES",
    "STYLE_ORDER",
    "TAG_BYTES",
    "WIDTH_PERCENT",
    "WORD_ALIGN",
]

MATCH_WEIGHT_LOW: Final = 400
MATCH_WEIGHT_HIGH: Final = 500
NORMAL_STRETCH: Final = 100.0
WIDTH_PERCENT: Final = {1: 50.0, 2: 62.5, 3: 75.0, 4: 87.5, 5: 100.0, 6: 112.5, 7: 125.0, 8: 150.0, 9: 200.0}
STYLES: Final = ("normal", "italic", "oblique")
STYLE_ORDER: Final = {
    "normal": ("normal", "oblique", "italic"),
    "italic": ("italic", "oblique", "normal"),
    "oblique": ("oblique", "italic", "normal"),
}
AXIS_WEIGHT: Final = "wght"
AXIS_WIDTH: Final = "wdth"
AXIS_SLANT: Final = "slnt"
TAG_BYTES: Final = 4
FONT_FILE_SUFFIXES: Final = frozenset({".ttf", ".otf", ".ttc", ".otc"})
STANDALONE_SUFFIXES: Final = frozenset({".ttf", ".otf"})
FONT_MIME: Final = {"truetype": "font/ttf", "opentype": "font/otf"}
CFF_TABLES: Final = frozenset({"CFF ", "CFF2"})
HEAD_TABLE: Final = "head"
HEAD_ADJUSTMENT: Final = slice(8, 12)
CHECKSUM_MAGIC: Final = 0xB1B0AFBA
SFNT_TRUETYPE: Final = 0x00010000
SFNT_CFF: Final = b"OTTO"
SFNT_HEADER: Final = ">4sHHHH"
SFNT_RECORD: Final = ">4sIII"
SFNT_CHECKSUM_MASK: Final = 0xFFFFFFFF
WORD_ALIGN: Final = 4
