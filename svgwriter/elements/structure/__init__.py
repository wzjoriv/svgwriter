"""Structural, descriptive and external-content elements."""

from __future__ import annotations

from ._containers import A, Defs, Group, Svg, Switch, Symbol, Use
from ._descriptive import Desc, Metadata, Title
from ._external import ColorProfile, StyleElement, View
from ._image import Image
from ._pixels import Pixels

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
