"""
Patterns rewritten in user space with their tile at the origin, the one form skia's SVG renderer tiles correctly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._constants import (
    OBJECT_BOUNDING_BOX,
    PAINT_PROPERTIES,
    PERCENT,
    TILE_COPY_SUFFIX,
    TILE_OFFSETS,
    USER_SPACE,
    VIEWPORT_AXES,
)
from .._tree import resolve

if TYPE_CHECKING:
    from ...elements.core import Element
    from ...pathdata.data import BBox

__all__ = ["user_space_patterns"]


def _tile(pattern: Element, box: BBox | None, extent: tuple[float, float]) -> list[float] | None:
    """``x``, ``y``, ``width``, ``height`` of the tile in user units, or None without a box to scale by."""
    from ...attributes.length import Length, Unit

    bounding = str(pattern.get("patternUnits", OBJECT_BOUNDING_BOX)) == OBJECT_BOUNDING_BOX
    if bounding and box is None:
        return None
    values = []
    for name, axis in VIEWPORT_AXES.items():
        length = Length.parse(pattern.get(name, 0))
        if bounding and box is not None:
            fraction = length.value / PERCENT if length.unit is Unit.PERCENT else length.value
            origin = (box.x, box.y)[axis] if name in TILE_OFFSETS else 0.0
            values.append(origin + (box.width, box.height)[axis] * fraction)
        elif length.unit is Unit.PERCENT:
            values.append(length.value * extent[axis] / PERCENT)
        else:
            values.append(length.to_user_units())
    return values


def _rewrite(pattern: Element, tile: list[float], box: BBox | None) -> None:
    from ...elements import Group

    x, y, width, height = tile
    content_box = str(pattern.get("patternContentUnits", USER_SPACE)) == OBJECT_BOUNDING_BOX
    if content_box and pattern.get("viewBox") is None and box is not None:
        children = [child for child in pattern if not isinstance(child, str)]
        for child in children:
            pattern.remove(child)
        holder = Group(*children)
        holder.attributes["transform"] = f"scale({box.width} {box.height})"
        pattern.add(holder)
    pattern.attributes.pop("patternContentUnits", None)
    transform = pattern.attributes.get("patternTransform")
    shift = f"translate({x} {y})"
    pattern.attributes["patternTransform"] = f"{_text(transform)} {shift}" if transform is not None else shift
    pattern.attributes.update(patternUnits=USER_SPACE, x=0, y=0, width=width, height=height)


def _text(value: object) -> str:
    return str(value.svg_value() if hasattr(value, "svg_value") else value)


def user_space_patterns(root: Element) -> None:
    """Rewrite every painted pattern into user space with its tile at the origin, in place.

    The tile offset moves into ``patternTransform``, bounding-box units become user units of
    the painted shape (a pattern shared by shapes of different boxes is copied per shape), and
    bounding-box content units become a scale on the content.

    Parameters
    ----------
    root : Element
        A render copy whose servers are self-contained (see ``resolve_servers``).

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._tiles import user_space_patterns
    >>> doc = svg.Document.from_string(
    ...     '<svg xmlns="http://www.w3.org/2000/svg"><pattern id="p" width=".5" height=".5"/>'
    ...     '<rect x="10" width="20" height="20" fill="url(#p)"/></svg>')
    >>> user_space_patterns(doc.root)
    >>> tile = doc.get_element_by_id(doc.root.find(svg.Rect).get("fill")[5:-1])
    >>> tile.get("width"), tile.get("patternTransform")
    (10.0, 'translate(10.0 0.0)')
    """
    from ._layers import viewport_extent

    rewritten: set[int] = set()
    serial = 0
    for element in list(root.iter()):
        for name in PAINT_PROPERTIES:
            pattern = resolve(element, element.attributes.get(name))
            if pattern is None or pattern.tag != "pattern" or id(pattern) in rewritten:
                continue
            measure = getattr(element, "local_bbox", None)
            try:
                box = measure() if measure is not None else None
            except (TypeError, ValueError):
                box = None
            tile = _tile(pattern, box, viewport_extent(pattern))
            if tile is None:
                continue
            per_shape = (str(pattern.get("patternUnits", OBJECT_BOUNDING_BOX)) == OBJECT_BOUNDING_BOX
                         or str(pattern.get("patternContentUnits", USER_SPACE)) == OBJECT_BOUNDING_BOX)
            if per_shape and pattern.parent is not None:
                serial += 1
                pattern = _copy(pattern, serial)
                element.attributes[name] = f"url(#{pattern.id})"
            _rewrite(pattern, tile, box)
            rewritten.add(id(pattern))


def _copy(pattern: Element, serial: int) -> Element:
    copy = pattern.clone()
    copy.attributes["id"] = f"{pattern.get('id')}{TILE_COPY_SUFFIX}{serial}"
    parent = pattern.parent
    assert parent is not None
    parent.insert(parent.children.index(pattern) + 1, copy)
    return copy
