"""
Inkscape rotation centres: ``inkscape:transform-center-x/y`` read into anchors and written back from them.

Inkscape stores the centre as an offset from the middle of the bounding box, in user units, with
the y axis pointing up; anchors are points in the element's own coordinates.
"""

from __future__ import annotations

from typing import Any

from ..elements.core import Element
from ._constants import CENTER_TOLERANCE, CENTER_X, CENTER_Y

__all__ = ["read_transform_centers", "transform_center"]


def _placeable(element: Element) -> bool:
    return hasattr(element, "anchor") and hasattr(element, "bounds")


def read_transform_centers(root: Element) -> None:
    """Turn every ``inkscape:transform-center-x/y`` pair under *root* into the element's anchor."""
    for element in root.iter():
        attributes = element.attributes
        if (CENTER_X not in attributes and CENTER_Y not in attributes) or not _placeable(element):
            continue
        box: Any = element.bounds()  # type: ignore[attr-defined]
        if box is None:
            continue
        try:
            dx, dy = float(attributes.get(CENTER_X, 0)), float(attributes.get(CENTER_Y, 0))
        except ValueError:
            continue
        centre = box.center
        element.anchor = element.t.inverse().apply(centre.x + dx, centre.y - dy)  # type: ignore[attr-defined]
        attributes.pop(CENTER_X, None)
        attributes.pop(CENTER_Y, None)


def transform_center(element: Element) -> dict[str, float]:
    """The ``inkscape:transform-center-x/y`` attributes for an element whose anchor was set, else nothing."""
    if getattr(element, "_anchor", None) is None or not _placeable(element):
        return {}
    box: Any = element.bounds()  # type: ignore[attr-defined]
    if box is None:
        return {}
    pivot = element.t.apply(*element.anchor)  # type: ignore[attr-defined]
    dx, dy = pivot.x - box.center.x, box.center.y - pivot.y
    if abs(dx) < CENTER_TOLERANCE and abs(dy) < CENTER_TOLERANCE:
        return {}
    return {CENTER_X: dx, CENTER_Y: dy}
