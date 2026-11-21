"""
Measuring, moving and stretching the children of a layout group.
"""

from __future__ import annotations

from typing import Any

from .._internal._fonts import font_size, font_weight, resolve_font
from ..elements import Transformable
from ..elements.core import Element
from ..pathdata.data import BBox
from ..transform.matrix import Matrix
from ._constants import RESIZABLE_TAGS, TOLERANCE

__all__ = ["extent", "move", "release", "resizable", "resize", "text_box"]

ASSIGNED = "_layout_assigned"
SIDES = ("width", "height")


def _transformed(box: BBox, matrix: Matrix) -> BBox:
    if matrix.is_identity:
        return box
    corners = ((box.x, box.y), (box.x + box.width, box.y), (box.x, box.y + box.height),
               (box.x + box.width, box.y + box.height))
    return BBox.from_points(matrix.apply(*corner) for corner in corners)


def text_box(text: Element) -> BBox | None:
    """The line box of a ``<text>`` in local coordinates: advances across, ascent to descent down.

    Unlike the tight glyph box, it does not depend on which letters are set, so ``"7"`` and ``"-"``
    labels of one size line up and take the same height.

    Parameters
    ----------
    text : Element
        A ``<text>`` element.

    Returns
    -------
    BBox or None
        The box, or None for empty text.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.layout._measure import text_box
    >>> text_box(svg.text("7", font_size=20)).height == text_box(svg.text("-", font_size=20)).height
    True
    """
    boxes = text.layout()  # type: ignore[attr-defined]
    if not boxes:
        return None
    metrics: dict[int, tuple[float, float]] = {}
    left = top = float("inf")
    right = bottom = float("-inf")
    for glyph in boxes:
        source = glyph.source if glyph.source is not None else text
        if id(source) not in metrics:
            font = resolve_font(str(source.computed("font-family", "sans-serif")),
                                font_size(source.computed("font-size", None)),
                                font_weight(source.computed("font-weight", "normal")),
                                str(source.computed("font-style", "")) in ("italic", "oblique"))
            measured = font.getMetrics()
            metrics[id(source)] = (-measured.fAscent, measured.fDescent)
        ascent, descent = metrics[id(source)]
        left, right = min(left, glyph.x), max(right, glyph.x + glyph.advance)
        top, bottom = min(top, glyph.y - ascent), max(bottom, glyph.y + descent)
    return BBox(left, top, right - left, bottom - top)


def extent(child: Element) -> BBox | None:
    """The box a layout gives *child*, in the group's coordinates.

    Text counts by its line box (:func:`text_box`), everything else by its
    :meth:`~svgwriter.elements.Transformable.bounds`.

    Parameters
    ----------
    child : Element
        A child of a layout group.

    Returns
    -------
    BBox or None
        The box, or None for children without extent (animations, titles), which the layout skips.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.layout._measure import extent
    >>> extent(svg.rect(0, 0, 4, 2).translate(1, 1)), extent(svg.Title("x"))
    (BBox(x=1.0, y=1.0, width=4.0, height=2.0), None)
    """
    if not isinstance(child, Transformable):
        return None
    if child.tag == "text":
        box = text_box(child)
        return None if box is None else _transformed(box, child.t)
    return child.bounds()


def move(child: Element, box: BBox, x: float, y: float) -> None:
    """Translate *child*, measured at *box*, so the box's top-left corner lands on ``(x, y)``.

    Parameters
    ----------
    child : Element
        A transformable child.
    box : BBox
        Its current :func:`extent`.
    x, y : float
        The target corner in the group's coordinates.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.layout._measure import move
    >>> r = svg.rect(0, 0, 4, 2)
    >>> move(r, r.bounds(), 5, 6)
    >>> r.bounds()
    BBox(x=5.0, y=6.0, width=4.0, height=2.0)
    """
    dx, dy = x - box.x, y - box.y
    if abs(dx) > TOLERANCE or abs(dy) > TOLERANCE:
        child.translate(dx, dy)  # type: ignore[attr-defined]


def resizable(child: Element) -> bool:
    """Whether a layout can stretch *child*: rects, images and layout groups.

    Parameters
    ----------
    child : Element
        A child of a layout group.

    Returns
    -------
    bool
        True when stretching sets its size.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.layout._measure import resizable
    >>> resizable(svg.rect(0, 0, 1, 1)), resizable(svg.circle(0, 0, 1))
    (True, False)
    """
    return child.tag in RESIZABLE_TAGS or hasattr(child, "_stretch")


def release(child: Element) -> None:
    """Undo an earlier stretch so *child* is measured at its own size.

    A size the user changed since the stretch is kept as the new natural size.

    Parameters
    ----------
    child : Element
        A child of a layout group.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.layout._measure import release, resize
    >>> r = svg.rect(0, 0, 4, 2)
    >>> resize(r, r.bounds(), 10, None)
    >>> release(r)
    >>> r.get("width")
    4
    """
    if hasattr(child, "_stretch"):
        child._stretch = (None, None)
        return
    assigned: dict[str, tuple[Any, float]] | None = child.__dict__.pop(ASSIGNED, None)
    for key, (natural, value) in (assigned or {}).items():
        if child.attributes.get(key) == value:
            child.attributes[key] = natural


def resize(child: Element, box: BBox, width: float | None, height: float | None) -> None:
    """Stretch a :func:`resizable` *child*, measured at *box*, to *width* and/or *height* in group units.

    Parameters
    ----------
    child : Element
        A resizable child.
    box : BBox
        Its current :func:`extent`.
    width, height : float or None
        The new size along each axis; None leaves that axis alone.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.layout._measure import resize
    >>> r = svg.rect(0, 0, 4, 2).scale(2, about="top_left")
    >>> resize(r, r.bounds(), 20, None)
    >>> r.get("width"), r.bounds().width
    (10.0, 20.0)
    """
    if hasattr(child, "_stretch"):
        child._stretch = (width, height)
        return
    local = child.local_bbox()  # type: ignore[attr-defined]
    assigned = dict(child.__dict__.get(ASSIGNED, {}))
    for key, target, measured, own in zip(SIDES, (width, height), (box.width, box.height),
                                          (local.width, local.height), strict=True):
        if target is None:
            continue
        value = target * own / measured if measured > TOLERANCE else target
        assigned.setdefault(key, (child.attributes.get(key), value))
        assigned[key] = (assigned[key][0], value)
        child.attributes[key] = value
    object.__setattr__(child, ASSIGNED, assigned)
