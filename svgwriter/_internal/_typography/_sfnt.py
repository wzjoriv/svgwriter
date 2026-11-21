"""
Font files rebuilt from a loaded face's tables, for faces that have no file of their own.
"""

from __future__ import annotations

import struct
from typing import Any

from ._font_constants import (
    CFF_TABLES,
    CHECKSUM_MAGIC,
    COLLECTION_COUNT,
    COLLECTION_OFFSETS_AT,
    HEAD_ADJUSTMENT,
    HEAD_TABLE,
    SFNT_CFF,
    SFNT_CHECKSUM_MASK,
    SFNT_HEADER,
    SFNT_RECORD,
    SFNT_TRUETYPE,
    WORD_ALIGN,
)
from ._font_match import axis_tag

__all__ = ["collection_member", "font_format", "sfnt_bytes"]


def font_format(tags: list[str]) -> str:
    """The ``@font-face`` format of a face with these tables: ``opentype`` for CFF outlines, else ``truetype``."""
    return "opentype" if CFF_TABLES & set(tags) else "truetype"


def _padded(data: bytes) -> bytes:
    return data + b"\0" * (-len(data) % WORD_ALIGN)


def _checksum(data: bytes) -> int:
    padded = _padded(data)
    return sum(struct.unpack(f">{len(padded) // WORD_ALIGN}I", padded)) & SFNT_CHECKSUM_MASK


def sfnt_bytes(typeface: Any) -> bytes:
    """A standalone TrueType/OpenType file holding every table of a skia typeface (one face of a collection)."""
    return _build({str(axis_tag(tag)): bytes(typeface.getTableData(tag)) for tag in typeface.getTableTags()})


def collection_member(blob: bytes, index: int) -> bytes:
    """Face *index* of a ``.ttc``/``.otc`` collection as a standalone font file, read from its table directory."""
    record = struct.calcsize(SFNT_RECORD)
    start = struct.unpack_from(COLLECTION_COUNT, blob, COLLECTION_OFFSETS_AT + index * struct.calcsize(COLLECTION_COUNT))[0]
    count = struct.unpack_from(SFNT_HEADER, blob, start)[1]
    tables = {}
    for at in range(start + struct.calcsize(SFNT_HEADER), start + struct.calcsize(SFNT_HEADER) + count * record, record):
        tag, _, offset, length = struct.unpack_from(SFNT_RECORD, blob, at)
        tables[tag.decode("latin-1")] = blob[offset:offset + length]
    return _build(tables)


def _build(tables: dict[str, bytes]) -> bytes:
    if HEAD_TABLE in tables:
        head = bytearray(tables[HEAD_TABLE])
        head[HEAD_ADJUSTMENT] = bytes(HEAD_ADJUSTMENT.stop - HEAD_ADJUSTMENT.start)
        tables[HEAD_TABLE] = bytes(head)
    count = len(tables)
    selector = max(count.bit_length() - 1, 0)
    search = (1 << selector) * struct.calcsize(SFNT_RECORD)
    version = SFNT_CFF if font_format(list(tables)) == "opentype" else SFNT_TRUETYPE.to_bytes(WORD_ALIGN, "big")
    header = struct.pack(SFNT_HEADER, version, count, search, selector, count * struct.calcsize(SFNT_RECORD) - search)
    offset = len(header) + count * struct.calcsize(SFNT_RECORD)
    records, bodies, head_at = [], [], None
    for tag in sorted(tables):
        data = tables[tag]
        head_at = offset if tag == HEAD_TABLE else head_at
        records.append(struct.pack(SFNT_RECORD, tag.encode("latin-1"), _checksum(data), offset, len(data)))
        bodies.append(_padded(data))
        offset += len(bodies[-1])
    font = bytearray(header + b"".join(records) + b"".join(bodies))
    if head_at is not None:
        adjustment = (CHECKSUM_MAGIC - _checksum(bytes(font))) & SFNT_CHECKSUM_MASK
        font[head_at + HEAD_ADJUSTMENT.start:head_at + HEAD_ADJUSTMENT.stop] = adjustment.to_bytes(WORD_ALIGN, "big")
    return bytes(font)
