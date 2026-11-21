"""
Family and style names read from a font's ``name`` table, typographic names first.
"""

from __future__ import annotations

import struct
from typing import Any

from ._font_constants import (
    COLLECTION_COUNT,
    COLLECTION_COUNT_AT,
    COLLECTION_TAG,
    ENGLISH_US,
    NAME_HEADER,
    NAME_PAIRS,
    NAME_PLATFORMS,
    NAME_RECORD,
    NAME_TABLE,
    REGULAR_SUBFAMILY,
)
from ._font_match import axis_tag

__all__ = ["face_count", "family_names"]


def _decode(platform: int, raw: bytes) -> str:
    return raw.decode("latin-1" if platform == NAME_PLATFORMS[-1] else "utf-16-be", errors="replace")


def _names(table: bytes) -> dict[int, str]:
    """English names by name ID, Windows records preferred over Unicode and Macintosh ones."""
    _, count, strings = struct.unpack_from(NAME_HEADER, table)
    found: dict[int, tuple[int, str]] = {}
    for index in range(count):
        platform, _, language, name_id, length, offset = struct.unpack_from(
            NAME_RECORD, table, struct.calcsize(NAME_HEADER) + index * struct.calcsize(NAME_RECORD))
        if platform not in NAME_PLATFORMS or (platform == NAME_PLATFORMS[0] and language != ENGLISH_US):
            continue
        rank = NAME_PLATFORMS.index(platform)
        if name_id not in found or rank < found[name_id][0]:
            found[name_id] = (rank, _decode(platform, table[strings + offset:strings + offset + length]))
    return {name_id: text for name_id, (_, text) in found.items()}


def family_names(typeface: Any) -> tuple[str, str]:
    """The family and subfamily of a face: typographic (IDs 16/17), then WWS (21/22), then legacy (1/2)."""
    data = typeface.getTableData(axis_tag(NAME_TABLE))
    names = _names(bytes(data)) if data else {}
    for family_id, subfamily_id in NAME_PAIRS:
        if names.get(family_id):
            return names[family_id], names.get(subfamily_id) or REGULAR_SUBFAMILY
    return typeface.getFamilyName(), REGULAR_SUBFAMILY


def face_count(blob: bytes) -> int:
    """How many faces a font file holds: the collection count of a ``.ttc``/``.otc``, else one."""
    if blob[:len(COLLECTION_TAG)] != COLLECTION_TAG:
        return 1
    return struct.unpack_from(COLLECTION_COUNT, blob, COLLECTION_COUNT_AT)[0]
