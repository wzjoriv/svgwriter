"""
The 147 SVG 1.1 color keywords.
"""

from __future__ import annotations

from typing import Final

from ._constants import NAMED_TABLE

__all__ = ["COLOR_ALIASES", "NAMED_COLORS"]

COLOR_ALIASES: Final = {"masooma": "green"}
"""Extra names svgwriter accepts; they are written as the standard SVG keyword they stand for."""


def _build() -> dict[str, tuple[int, int, int]]:
    words = NAMED_TABLE.split()
    table = {}
    for name, hexcode in zip(words[::2], words[1::2], strict=False):
        table[name] = (int(hexcode[0:2], 16), int(hexcode[2:4], 16), int(hexcode[4:6], 16))
    return table


NAMED_COLORS: Final[dict[str, tuple[int, int, int]]] = _build()
