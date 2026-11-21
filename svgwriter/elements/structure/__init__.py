"""Structural, descriptive and external-content elements."""

from __future__ import annotations

from ._containers import Defs, Group
from ._descriptive import Desc, Metadata, Title
from ._external import ColorProfile, StyleElement, View
from ._image import Image
from ._link import A, Use
from ._pixels import Pixels
from ._svg import Svg
from ._symbol import Switch, Symbol

__all__ = [
    "A",
    "ColorProfile",
    "Defs",
    "Desc",
    "Group",
    "Image",
    "Pixels",
    "Metadata",
    "StyleElement",
    "Svg",
    "Switch",
    "Symbol",
    "Title",
    "Use",
    "View",
]
