"""
Paint servers made self-contained on a render copy: ``xlink:href`` templates merged in, radial focal points clamped.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .._constants import (
    GRADIENT_TAGS,
    NONE,
    OBJECT_BOUNDING_BOX,
    PAINT_PROPERTIES,
    PERCENT,
    SERVER_ATTRIBUTES,
    SERVER_UNITS,
    URL_PREFIX,
    XLINK_HREF,
)
from .._tree import resolve

if TYPE_CHECKING:
    from ...model.elements.core import Element

__all__ = ["resolve_servers"]


def _merge(server: Element, done: set[int], chain: set[int]) -> None:
    """Copy into *server* what it inherits through its ``xlink:href`` chain, then drop the link."""
    if id(server) in done:
        return
    chain.add(id(server))
    template = resolve(server, server.attributes.pop(XLINK_HREF, None))
    if template is not None and id(template) not in chain and template.tag in SERVER_ATTRIBUTES:
        same_family = (template.tag in GRADIENT_TAGS) == (server.tag in GRADIENT_TAGS)
        if same_family:
            _merge(template, done, chain)
            for name in SERVER_ATTRIBUTES[server.tag]:
                if name not in server.attributes and name in template.attributes:
                    server.attributes[name] = template.attributes[name]
            content = [child for child in template if not isinstance(child, str)
                       and (server.tag not in GRADIENT_TAGS or child.tag == "stop")]
            if not any(not isinstance(child, str) for child in server) and content:
                for child in content:
                    server.add(child.clone())
    done.add(id(server))


def _fraction(value: object, default: float) -> tuple[float, bool]:
    from ...model.attributes.length import Length, Unit

    if value is None:
        return default, False
    length = Length.parse(value)
    return (length.value / PERCENT, True) if length.unit is Unit.PERCENT else (length.to_user_units(), False)


def _clamp_focus(gradient: Element) -> None:
    """Move a focal point outside the end circle onto it, as SVG 1.1 asks."""
    centre = [_fraction(gradient.get(name), 0.5) for name in ("cx", "cy")]
    radius, _ = _fraction(gradient.get("r"), 0.5)
    focus = [_fraction(gradient.get(f), c[0]) if gradient.get(f) is not None else c
             for f, c in zip(("fx", "fy"), centre, strict=True)]
    dx, dy = focus[0][0] - centre[0][0], focus[1][0] - centre[1][0]
    distance = math.hypot(dx, dy)
    if distance <= radius or not distance:
        return
    scale = radius / distance
    for name, (value, percent), offset in zip(("fx", "fy"), centre, (dx, dy), strict=True):
        moved = value + offset * scale
        gradient.attributes[name] = f"{moved * PERCENT}%" if percent else moved


def resolve_servers(root: Element) -> None:
    """Make every gradient and pattern under *root* self-contained, in place.

    Attributes and content a server leaves out are taken from the server its ``xlink:href``
    names (recursively, gradients from gradients and patterns from patterns). A radial
    gradient's focal point outside its circle moves onto the circle. Paint that names a
    gradient without stops becomes ``none``; paint naming no server or a pattern with an empty
    tile, or in bounding-box units on a shape with no width or height, becomes its fallback
    colour (or ``none``). A link to nothing is ignored.

    Parameters
    ----------
    root : Element
        A render copy; it is changed in place.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._servers import resolve_servers
    >>> doc = svg.Document.from_string(
    ...     '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
    ...     '<linearGradient id="a" x2="0"><stop offset="0"/></linearGradient>'
    ...     '<linearGradient id="b" xlink:href="#a"/></svg>')
    >>> resolve_servers(doc.root)
    >>> b = doc.get_element_by_id("b")
    >>> b.get("x2"), [child.tag for child in b]
    ('0', ['stop'])
    """
    servers = [e for e in root.iter() if e.tag in SERVER_ATTRIBUTES]
    done: set[int] = set()
    for server in servers:
        _merge(server, done, set())
    for server in servers:
        if server.tag == "radialGradient":
            _clamp_focus(server)
    empty = {id(s) for s in servers if s.tag in GRADIENT_TAGS and not any(c.tag == "stop" for c in s
                                                                           if not isinstance(c, str))}
    for element in root.iter():
        for name in PAINT_PROPERTIES:
            value = element.attributes.get(name)
            text = str(value.svg_value() if hasattr(value, "svg_value") else value).strip()
            if not text.startswith(URL_PREFIX):
                continue
            link, _, fallback = text.partition(")")
            fallback = fallback.strip()
            target = getattr(value, "element", None) or resolve(element, f"{link})")
            usable = target is not None and target.tag in SERVER_ATTRIBUTES
            if usable and id(target) in empty:
                element.attributes[name] = NONE
            elif not usable or _empty_tile(target) or _degenerate(element, target):
                element.attributes[name] = fallback or NONE
            elif fallback:
                element.attributes[name] = f"{link})"


def _empty_tile(server: Element) -> bool:
    """Whether *server* is a pattern whose tile has no area, which disables the paint."""
    from ...model.attributes.length import Length

    if server.tag != "pattern":
        return False
    return any(Length.parse(server.get(name, 0)).value == 0 for name in ("width", "height"))


def _degenerate(element: Element, server: Element) -> bool:
    """Whether *server* is in bounding-box units and *element*'s box has no width or no height."""
    units = SERVER_UNITS[server.tag]
    if str(server.get(units, OBJECT_BOUNDING_BOX)) != OBJECT_BOUNDING_BOX:
        return False
    measure = getattr(element, "local_bbox", None)
    try:
        box = measure() if measure is not None else None
    except (TypeError, ValueError):
        return False
    return box is not None and (not box.width or not box.height)
