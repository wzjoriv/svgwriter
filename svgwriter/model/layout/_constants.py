"""
Constants for layout groups: alignment and distribution names, track keywords and resizable tags.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "ALIGNMENTS",
    "ALIGN_SHARE",
    "AUTO",
    "CENTER",
    "DISTRIBUTIONS",
    "END",
    "FR",
    "GRID_ALIGN",
    "IMPLICIT_TRACK",
    "RESIZABLE_TAGS",
    "SPACE_AROUND",
    "SPACE_BETWEEN",
    "SPACE_EVENLY",
    "SPACER_GROW",
    "STACK_ALIGN",
    "START",
    "STRETCH",
    "TOLERANCE",
]

START: Final = "start"
CENTER: Final = "center"
END: Final = "end"
STRETCH: Final = "stretch"
SPACE_BETWEEN: Final = "space_between"
SPACE_AROUND: Final = "space_around"
SPACE_EVENLY: Final = "space_evenly"

ALIGNMENTS: Final = (START, CENTER, END, STRETCH)
"""Placement of a child across its slot (the cross axis of a stack, either axis of a grid cell)."""
DISTRIBUTIONS: Final = (START, CENTER, END, SPACE_BETWEEN, SPACE_AROUND, SPACE_EVENLY)
"""Distribution of free space along a stack's main axis."""

ALIGN_SHARE: Final = {START: 0.0, CENTER: 0.5, END: 1.0, STRETCH: 0.0}
"""Fraction of the free space placed before a child for each alignment."""

STACK_ALIGN: Final = START
"""Default cross-axis alignment of a stack."""
GRID_ALIGN: Final = STRETCH
"""Default alignment of a child in its grid cell."""

AUTO: Final = "auto"
"""Track sized to its largest child."""
FR: Final = "fr"
"""Suffix of a flexible track (``"1fr"``, ``"2fr"``)."""
IMPLICIT_TRACK: Final = "1fr"
"""Size of tracks given only by a count, or created for children past the explicit rows."""

SPACER_GROW: Final = 1.0
"""Default share of the free space a spacer takes."""

RESIZABLE_TAGS: Final = frozenset({"rect", "image"})
"""Tags whose ``width`` and ``height`` a layout may set to stretch them."""

TOLERANCE: Final = 1e-9
"""Moves and resizes smaller than this are skipped, so laying out twice changes nothing."""
