"""
What a batch holds: the element class of its items, their geometry columns and their boxes.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np

from ..elements.core import Element
from ..elements.shapes import Circle, Line, Polygon, Polyline, Rect
from ..elements.structure import Use
from ..elements.text import Text

__all__ = ["CIRCLES", "INSTANCES", "Kind", "LINES", "POLYGONS", "POLYLINES", "RECTS", "TEXTS", "Geometry"]


@dataclass(frozen=True)
class Geometry:
    """The geometry of a batch's items: their columns and, for point lists, the flat points."""

    columns: Mapping[str, np.ndarray]
    points: np.ndarray | None = None
    offsets: np.ndarray | None = None


Boxes = Callable[[Geometry], np.ndarray]


@dataclass(frozen=True)
class Kind:
    """One sort of batch item.

    Attributes
    ----------
    element : type
        The class each item is when the batch expands.
    geometry : tuple of str
        Attributes that place the item, written first.
    boxes : callable or None
        ``boxes(geometry)``: each item's ``(x0, y0, x1, y1)`` box as an ``(N, 4)`` array, before its
        transform; None when the box needs measuring (text) or comes from a shape (instances).
    """

    element: type[Element]
    geometry: tuple[str, ...]
    boxes: Boxes | None = None


def _circle_boxes(geometry: Geometry) -> np.ndarray:
    cx, cy, r = (geometry.columns[name] for name in ("cx", "cy", "r"))
    return np.stack([cx - r, cy - r, cx + r, cy + r], axis=1)


def _rect_boxes(geometry: Geometry) -> np.ndarray:
    x, y, width, height = (geometry.columns[name] for name in ("x", "y", "width", "height"))
    return np.stack([x, y, x + width, y + height], axis=1)


def _line_boxes(geometry: Geometry) -> np.ndarray:
    x1, y1, x2, y2 = (geometry.columns[name] for name in ("x1", "y1", "x2", "y2"))
    return np.stack([np.minimum(x1, x2), np.minimum(y1, y2), np.maximum(x1, x2), np.maximum(y1, y2)], axis=1)


def _point_boxes(geometry: Geometry) -> np.ndarray:
    assert geometry.points is not None and geometry.offsets is not None
    starts = geometry.offsets[:-1]
    low = np.minimum.reduceat(geometry.points, starts, axis=0)
    high = np.maximum.reduceat(geometry.points, starts, axis=0)
    return np.concatenate([low, high], axis=1)


CIRCLES = Kind(Circle, ("cx", "cy", "r"), _circle_boxes)
RECTS = Kind(Rect, ("x", "y", "width", "height"), _rect_boxes)
LINES = Kind(Line, ("x1", "y1", "x2", "y2"), _line_boxes)
POLYLINES = Kind(Polyline, (), _point_boxes)
POLYGONS = Kind(Polygon, (), _point_boxes)
TEXTS = Kind(Text, ("x", "y"))
INSTANCES = Kind(Use, ())
