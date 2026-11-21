"""
Filter geometry in an element's user space: the filter region, primitive subregions and ``<feImage>`` sources.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import skia

from .._internal._constants import OBJECT_BOUNDING_BOX, PERCENT, USER_SPACE, VIEWPORT_AXES
from ._constants import CHANNEL_MAX, FILTER_REGION_DEFAULT

if TYPE_CHECKING:
    from ..elements.core import Element
    from ..pathdata.data import BBox

__all__ = ["Frame", "filter_region", "image_source"]


def _length(value: object, extent: float, bounding: bool, origin: float) -> float:
    """One region coordinate: a fraction (or percentage) of *extent* past *origin*, or a user length."""
    from ..attributes.length import Length, Unit

    length = Length.parse(value)
    if bounding:
        fraction = length.value / PERCENT if length.unit is Unit.PERCENT else length.value
        return origin + fraction * extent
    return length.value * extent / PERCENT if length.unit is Unit.PERCENT else length.to_user_units()


def _rect(element: Element, box: BBox | None, viewport: tuple[float, float], bounding: bool,
          default: skia.Rect) -> skia.Rect | None:
    """The ``x``/``y``/``width``/``height`` of *element* as a rect, unset values taken from *default*."""
    if bounding and box is None:
        return None
    sizes = (box.width, box.height) if bounding and box is not None else viewport
    origins = (box.x, box.y) if bounding and box is not None else (0.0, 0.0)
    fallback = {"x": default.left(), "y": default.top(), "width": default.width(), "height": default.height()}
    values = {}
    for name, axis in VIEWPORT_AXES.items():
        value = element.get(name)
        values[name] = fallback[name] if value is None else _length(
            value, sizes[axis], bounding, origins[axis] if name in ("x", "y") else 0.0)
    return skia.Rect.MakeXYWH(values["x"], values["y"], values["width"], values["height"])


def filter_region(filter_element: Element, box: BBox | None, viewport: tuple[float, float]) -> skia.Rect | None:
    """The filter region in the filtered element's user space, or None when it cannot be placed.

    Parameters
    ----------
    filter_element : Element
        The ``<filter>``.
    box : BBox or None
        The filtered element's bounding box in its user space.
    viewport : tuple of (float, float)
        The viewport size percentages in user units resolve against.

    Returns
    -------
    skia.Rect or None
        The region; None in bounding-box units without a box.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.pathdata.data import BBox
    >>> from svgwriter.ops._filter_frame import filter_region
    >>> filter_region(svg.Filter(), BBox(0, 0, 10, 10), (100, 100)).width()
    12.0
    """
    bounding = str(filter_element.get("filterUnits", OBJECT_BOUNDING_BOX)) != USER_SPACE
    if bounding and box is None:
        return None
    start, size = FILTER_REGION_DEFAULT
    if bounding and box is not None:
        default = skia.Rect.MakeXYWH(box.x + start * box.width, box.y + start * box.height,
                                     size * box.width, size * box.height)
    else:
        default = skia.Rect.MakeXYWH(start * viewport[0], start * viewport[1], size * viewport[0], size * viewport[1])
    return _rect(filter_element, box, viewport, bounding, default)


@dataclass
class Frame:
    """Where a filter runs: the filtered element's box, the filter region and the ``feImage`` loader.

    Attributes
    ----------
    box : BBox or None
        The filtered element's bounding box in its user space.
    region : skia.Rect
        The filter region in the same space.
    viewport : tuple of (float, float)
        Percentages of user-space lengths resolve against it.
    bounding : bool
        ``primitiveUnits`` is ``objectBoundingBox``.
    element_source : callable
        Draws a referenced element (``feImage`` with ``#id``) as a picture in this space.
    inputs : dict of str to skia.ImageFilter
        The standard inputs besides the source (``BackgroundImage``, ``FillPaint``, ...) the filter reads.
    """

    box: BBox | None
    region: skia.Rect
    viewport: tuple[float, float]
    bounding: bool
    element_source: Callable[[Element], Any]
    inputs: dict[str, Any] = field(default_factory=dict)

    @property
    def scale(self) -> tuple[float, float]:
        """User units per primitive unit along x and y: the box size in bounding-box units, else 1."""
        if self.bounding and self.box is not None:
            return (self.box.width, self.box.height)
        return (1.0, 1.0)

    def placement(self, primitive: Element) -> skia.Rect:
        """The primitive subregion of *primitive* as given, before clipping; where ``feImage`` fits its picture.

        Parameters
        ----------
        primitive : Element
            An ``fe*`` element; the coordinates it leaves out come from the filter region.

        Returns
        -------
        skia.Rect
            The unclipped subregion.
        """
        return _rect(primitive, self.box, self.viewport, self.bounding, self.region) or self.region

    def subregion(self, primitive: Element, default: skia.Rect) -> skia.Rect:
        """The primitive subregion of *primitive*, clipped to the filter region.

        Parameters
        ----------
        primitive : Element
            An ``fe*`` element.
        default : skia.Rect
            Used for the coordinates the primitive leaves out.

        Returns
        -------
        skia.Rect
            The subregion.
        """
        rect = _rect(primitive, self.box, self.viewport, self.bounding, default) or default
        clipped = skia.Rect(rect.left(), rect.top(), rect.right(), rect.bottom())
        return clipped if clipped.intersect(self.region) else skia.Rect.MakeEmpty()


def _fitted(columns: int, rows: int, area: skia.Rect, ratio_text: object) -> skia.Rect:
    from .._internal._render._layers import fit_box
    from ..attributes.viewbox import PreserveAspectRatio

    ratio = ratio_text if isinstance(ratio_text, PreserveAspectRatio) else (
        PreserveAspectRatio.parse(str(ratio_text)) if ratio_text is not None else PreserveAspectRatio())
    m = fit_box(area.width(), area.height(), columns, rows, ratio)
    return skia.Rect.MakeXYWH(area.left() + m.e, area.top() + m.f, columns * m.a, rows * m.d)


def image_source(primitive: Element, area: skia.Rect, frame: Frame) -> Any:
    """``<feImage>`` as a skia image filter drawing into *area*; None when its link cannot be drawn.

    Parameters
    ----------
    primitive : Element
        The ``<feImage>``; its link is embedded pixels or ``#id``.
    area : skia.Rect
        The primitive subregion.
    frame : Frame
        The filter's frame.

    Returns
    -------
    skia.ImageFilter or None
        The source.
    """
    from ..elements.structure import Pixels

    link = primitive.attributes.get("xlink:href")
    if isinstance(link, Pixels):
        rgba = link.rgba()
        premultiplied = np.concatenate([rgba[..., :3] * rgba[..., 3:], rgba[..., 3:]], axis=-1)
        pixels = np.ascontiguousarray(np.clip(np.rint(premultiplied * CHANNEL_MAX), 0, CHANNEL_MAX).astype(np.uint8))
        image = skia.Image.fromarray(pixels, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        rows, columns = pixels.shape[:2]
        placed = _fitted(columns, rows, area, primitive.get("preserveAspectRatio"))
        return skia.ImageFilters.Image(image, skia.Rect.MakeWH(columns, rows), placed,
                                       skia.SamplingOptions(skia.FilterMode.kLinear))
    target = getattr(link, "element", None)
    if target is None and isinstance(link, str) and link.startswith("#"):
        target = primitive.root().get_element_by_id(link[1:])
    if target is None:
        return None
    return skia.ImageFilters.Picture(frame.element_source(target), area)
