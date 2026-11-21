"""
Grapheme clusters: where user-perceived characters start in a string.
"""

from __future__ import annotations

import unicodedata

from ._constants import JOINING_RANGES, REGIONAL_INDICATORS, ZWJ

__all__ = ["cluster_bounds"]


def _joins(previous: str, char: str) -> bool:
    """Whether *char* continues the cluster that *previous* ended."""
    code = ord(char)
    if char == ZWJ or previous == ZWJ or unicodedata.category(char) in ("Mn", "Me", "Mc"):
        return True
    return any(low <= code <= high for low, high in JOINING_RANGES)


def cluster_bounds(text: str) -> list[int]:
    """Start offsets of the user-perceived characters (grapheme clusters) of *text*, plus ``len(text)``.

    Combining marks, ZWJ emoji sequences, variation selectors, skin tones, tag
    sequences, keycaps and regional-indicator pairs (flags) stay with their
    base character, so ``"é"`` is one character, not two.

    Examples
    --------
    >>> cluster_bounds("éx")
    [0, 2, 3]
    """
    bounds: list[int] = []
    regional_run = 0
    for index, char in enumerate(text):
        regional = REGIONAL_INDICATORS[0] <= ord(char) <= REGIONAL_INDICATORS[1]
        pairs_up = regional and regional_run % 2 == 1
        if index == 0 or not (pairs_up or _joins(text[index - 1], char)):
            bounds.append(index)
        regional_run = regional_run + 1 if regional else 0
    return [*bounds, len(text)]
