"""
The ``viewBox``/``preserveAspectRatio`` attribute group and positioning.
"""

from __future__ import annotations

from typing import Any

from ...attributes.descriptors import LengthAttr
from ...attributes.viewbox import PreserveAspectRatio, ViewBox
from ...pathdata.data import BBox
from ...units.lengths import Length, LengthLike
from ..core import Child, Element

__all__ = ["FitToViewBox", "Positioned", "ViewBoxLike", "positioned_bbox", "user_units"]

ViewBoxLike = ViewBox | tuple[float, float, float, float] | str


def user_units(value: Any) -> float:
    """A length attribute in user units; unset counts as zero.

    Parameters
    ----------
    value : length or None
        A length value such as ``"1in"`` or a number.

    Returns
    -------
    float
        The length in user units.

    Examples
    --------
    >>> from svgwriter.model.elements._behavior._viewport import user_units
    >>> user_units(None), user_units("1in")
    (0.0, 96.0)
    """
    return 0.0 if value is None else Length.parse(value).to_user_units()


def positioned_bbox(element: Element) -> BBox | None:
    """``x``/``y``/``width``/``height`` as a box, or ``None`` without a size.

    Parameters
    ----------
    element : Element
        An element with ``width`` and ``height`` attributes.

    Returns
    -------
    BBox or None
        The box, or None when a dimension is missing or a percentage.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.elements._behavior._viewport import positioned_bbox
    >>> positioned_bbox(svg.image("a.png", 1, 2, 3, 4))
    BBox(x=1.0, y=2.0, width=3.0, height=4.0)
    """
    width, height = element.get("width"), element.get("height")
    if width is None or height is None or "%" in str(width) or "%" in str(height):
        return None
    return BBox(user_units(element.get("x")), user_units(element.get("y")), user_units(width), user_units(height))


class FitToViewBox(Element):
    """Elements that establish a viewBox.

    Parameters
    ----------
    *args : Element or str
        Children.
    view_box : ViewBox, tuple or str, optional
        The ``viewBox``. Defaults to None.
    preserve_aspect_ratio : PreserveAspectRatio or str, optional
        How the view box fits the viewport. Defaults to None.
    **kwargs
        Passed on to the next base class.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.symbol(view_box=(0, 0, 10, 10)).view_box.width
    10
    """

    def __init__(
        self,
        *args: Child,
        view_box: ViewBoxLike | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.view_box = view_box  # type: ignore[assignment]
        self._assign(preserve_aspect_ratio=preserve_aspect_ratio)

    @property
    def view_box(self) -> ViewBox | None:
        """The ``viewBox`` as a :class:`~svgwriter.ViewBox`, or None; assign a tuple or string to set it.

        Examples
        --------
        >>> import svgwriter as svg
        >>> s = svg.symbol(view_box="0 0 4 2")
        >>> s.view_box.height
        2.0
        """
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
    """``x``, ``y``, ``width`` and ``height`` keywords.

    Parameters
    ----------
    *args : Element or str
        Children.
    x, y : length, optional
        Position. Defaults to None.
    width, height : length, optional
        Size. Defaults to None.
    **kwargs
        Passed on to the next base class.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.image("a.png", 1, 2, 3, 4).width
    3.0
    """

    x = LengthAttr()
    y = LengthAttr()
    width = LengthAttr()
    height = LengthAttr()

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
        self._assign(x=x, y=y, width=width, height=height)
