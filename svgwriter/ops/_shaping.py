"""
HarfBuzz access for shaping complex scripts.
"""

from __future__ import annotations

from typing import Any

__all__ = ["harfbuzz", "hb_font"]


_HB_FONTS: dict[int, Any] = {}


def harfbuzz() -> Any:
    """The ``uharfbuzz`` module, or None when it is not installed."""
    try:
        import uharfbuzz
    except ImportError:
        return None
    return uharfbuzz


def hb_font(typeface: Any) -> Any:
    """A HarfBuzz font reading *typeface*'s tables through skia (cached; table bytes kept alive)."""
    key = typeface.uniqueID()
    if key not in _HB_FONTS:
        hb = harfbuzz()
        tables: dict[str, bytes] = {}

        def table(face: Any, tag: str, data: Any) -> bytes:
            raw = typeface.copyTableData(int.from_bytes(tag.encode("latin-1"), "big"))
            tables[tag] = bytes(raw) if raw is not None else b""
            return tables[tag]

        face = hb.Face.create_for_tables(table, None)
        _HB_FONTS[key] = (hb.Font(face), face.upem, tables, table)
    return _HB_FONTS[key]
