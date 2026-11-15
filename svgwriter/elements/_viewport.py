"""The ``viewBox``/``preserveAspectRatio`` attribute group and positioning."""

from __future__ import annotations

from typing import Any

from ..attributes.descriptors import Attr
from ..attributes.length import Length, LengthLike
from ..attributes.viewbox import PreserveAspectRatio, ViewBox
from ..path.data import BBox
from .base import Child, Element

__all__ = ["FitToViewBox", "Positioned", "ViewBoxLike", "positioned_bbox", "user_units"]

ViewBoxLike = ViewBox | tuple[float, float, float, float] | str


def user_units(value: Any) -> float:
    """A length attribute in user units; unset counts as zero."""
    return 0.0 if value is None else Length.parse(value).to_user_units()


def positioned_bbox(element: Element) -> BBox | None:
    """``x``/``y``/``width``/``height`` as a box, or ``None`` without a size."""
    width, height = element.get("width"), element.get("height")
    if width is None or height is None or "%" in str(width) or "%" in str(height):
        return None
    return BBox(user_units(element.get("x")), user_units(element.get("y")), user_units(width), user_units(height))


class FitToViewBox(Element):
    """Elements that establish a viewBox."""

    def __init__(
        self,
        *args: Child,
        view_box: ViewBoxLike | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.view_box = view_box  # type: ignore[assignment]
        self.update(preserve_aspect_ratio=preserve_aspect_ratio)

    @property
    def view_box(self) -> ViewBox | None:
        raw = self.attributes.get("viewBox")
        if raw is None or isinstance(raw, ViewBox):
            return raw
        return ViewBox.parse(str(raw))

    @view_box.setter
    def view_box(self, value: ViewBoxLike | None) -> None:
        if value is None:
            self.attributes.pop("viewBox", None)
        elif isinstance(value, str):
            self.attributes["viewBox"] = ViewBox.parse(value)
        else:
            self.attributes["viewBox"] = ViewBox(*value)


class Positioned(Element):
    """``x``, ``y``, ``width`` and ``height`` keywords."""

    x = Attr[Length](convert=Length.parse)
    y = Attr[Length](convert=Length.parse)
    width = Attr[Length](convert=Length.parse)
    height = Attr[Length](convert=Length.parse)

    def __init__(
        self,
        *args: Child,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        width: LengthLike | None = None,
        height: LengthLike | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.update(x=x, y=y, width=width, height=height)
