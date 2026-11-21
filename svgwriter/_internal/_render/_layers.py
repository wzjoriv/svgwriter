"""
Paint order, viewports and image placement shared by the renderer and the exporters.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from .._constants import CONTAINERS, NOT_RENDERED, VIEWPORT_FALLBACK

if TYPE_CHECKING:
    from ...attributes.viewbox import PreserveAspectRatio
    from ...elements.core import Element
    from ...elements.structure import Image
    from ...pathdata.data import BBox
    from ...transform.matrix import Matrix

__all__ = ["ancestry", "drawable_order", "fit_box", "image_matrix", "image_viewport", "pixel_box", "viewport_extent"]


def drawable_order(root: Element, atomic: Callable[[Element], bool] | None = None) -> list[Element]:
    """Rendered leaf elements in paint order (containers and definitions skipped).

    Walks the tree depth first, descending into ``svg``, ``g``, ``a`` and ``switch`` and
    skipping definition-only elements such as ``defs``, ``clipPath`` and gradients.

    Parameters
    ----------
    root : Element
        The element whose descendants are listed.
    atomic : callable, optional
        Containers it accepts are listed as one leaf instead of being entered. Defaults to None.

    Returns
    -------
    list of Element
        Leaf elements, first painted first.

    See Also
    --------
    svgwriter.ops._raster._layers.layers : Group the same leaves into runs around embedded images.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._layers import drawable_order
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 5, 5)
    >>> _ = doc.circle(5, 5, 2)
    >>> [e.tag for e in drawable_order(doc.root)]
    ['rect', 'circle']
    """
    order: list[Element] = []

    def visit(node: Element) -> None:
        for child in node:
            if child.tag in NOT_RENDERED:
                continue
            if child.tag in CONTAINERS and not (atomic is not None and atomic(child)):
                visit(child)
            else:
                order.append(child)

    if root.tag in CONTAINERS:
        visit(root)
    elif root.tag not in NOT_RENDERED:
        order.append(root)
    return order


def viewport_extent(element: Element) -> tuple[float, float]:
    """The width and height of the viewport *element* sits in, which percentages resolve against.

    Parameters
    ----------
    element : Element
        Any element in a tree.

    Returns
    -------
    tuple of (float, float)
        The nearest ``<svg>`` ancestor's ``viewBox`` size, else its absolute ``width`` and
        ``height``, else the next viewport up; 300 by 300 when none is sized.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._layers import viewport_extent
    >>> doc = svg.Document(40, 30)
    >>> viewport_extent(doc.rect(0, 0, 1, 1))
    (40.0, 30.0)
    """
    from ...attributes.length import Length, Unit
    from ...attributes.viewbox import ViewBox

    node = element.parent
    while node is not None:
        if node.tag == "svg":
            box = node.get("viewBox")
            box = box if isinstance(box, ViewBox) or box is None else ViewBox.parse(str(box))
            if box is not None and box.width and box.height:
                return float(box.width), float(box.height)
            sizes = [node.get(name) for name in ("width", "height")]
            if all(size is not None and Length.parse(size).unit is not Unit.PERCENT for size in sizes):
                return float(Length.parse(sizes[0]).to_user_units()), float(Length.parse(sizes[1]).to_user_units())
        node = node.parent
    return VIEWPORT_FALLBACK, VIEWPORT_FALLBACK


def _number(value: object, default: float = 0.0) -> float:
    from ...attributes.length import Length

    return default if value is None else Length.parse(value).to_user_units()


def fit_box(box_w: float, box_h: float, w: float, h: float, ratio: PreserveAspectRatio) -> Matrix:
    """Map a *w* by *h* area into a *box_w* by *box_h* box as ``preserveAspectRatio`` *ratio* says."""
    from ...attributes.viewbox import Align, MeetOrSlice
    from ...transform.matrix import Matrix

    sx, sy = box_w / w, box_h / h
    if ratio.align is Align.NONE:
        return Matrix.scale(sx, sy)
    s = max(sx, sy) if ratio.meet_or_slice is MeetOrSlice.SLICE else min(sx, sy)
    name = ratio.align.value
    fx = {"xMin": 0.0, "xMid": 0.5, "xMax": 1.0}[name[:4]]
    fy = {"YMin": 0.0, "YMid": 0.5, "YMax": 1.0}[name[4:]]
    return Matrix.translate((box_w - w * s) * fx, (box_h - h * s) * fy) @ Matrix.scale(s)


def image_matrix(image: Image) -> Matrix:
    """Map pixel coordinates of *image* to its parent's user space (``t`` excluded).

    Combines the image's ``x``/``y`` offset with the scale and alignment given by its
    ``width``, ``height`` and ``preserveAspectRatio``.

    Parameters
    ----------
    image : Image
        An ``<image>`` element holding embedded pixels.

    Returns
    -------
    Matrix
        The pixel-to-user-space transform.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._layers import image_matrix
    >>> picture = svg.Image(np.zeros((2, 2, 4)), 10, 20, 4, 4)
    >>> (image_matrix(picture).e, image_matrix(picture).f)
    (10.0, 20.0)
    """
    from ...attributes.viewbox import PreserveAspectRatio
    from ...transform.matrix import Matrix

    rows, columns = image.shape
    ratio_text = image.get("preserveAspectRatio")
    ratio = ratio_text if isinstance(ratio_text, PreserveAspectRatio) else (
        PreserveAspectRatio.parse(str(ratio_text)) if ratio_text is not None else PreserveAspectRatio()
    )
    fit = fit_box(_number(image.get("width"), columns), _number(image.get("height"), rows), columns, rows, ratio)
    return Matrix.translate(_number(image.get("x")), _number(image.get("y"))) @ fit


def image_viewport(image: Image) -> BBox | None:
    """The ``x``/``y``/``width``/``height`` box of *image* in user units, or None without a size.

    Parameters
    ----------
    image : Image
        An ``<image>`` element.

    Returns
    -------
    BBox or None
        The viewport its picture is fitted into and clipped to.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._layers import image_viewport
    >>> image_viewport(svg.Image("a.png", 1, 2, 3, 4))
    BBox(x=1.0, y=2.0, width=3.0, height=4.0)
    """
    from ...pathdata.data import BBox

    if image.get("width") is None or image.get("height") is None:
        return None
    return BBox(_number(image.get("x")), _number(image.get("y")), _number(image.get("width")),
                _number(image.get("height")))


def ancestry(element: Element, root: Element) -> tuple[Matrix, float]:
    """The transform and opacity *element* collects from itself up to *root* (an outer ``<svg>`` root excluded)."""
    from ...elements import Transformable
    from ...transform.matrix import IDENTITY

    matrix, opacity = IDENTITY, 1.0
    node: Element | None = element
    while node is not None:
        if node is root and root.tag == "svg":
            break
        if isinstance(node, Transformable):
            matrix = node.t @ matrix
        opacity *= float(node.get("opacity", 1.0))
        if node is root:
            break
        node = node.parent
    return matrix, opacity


def pixel_box(image: Image, matrix: Matrix) -> BBox:
    """The upright box covering the pixel grid of *image* placed by *matrix*.

    Parameters
    ----------
    image : Image
        An ``<image>`` element holding embedded pixels.
    matrix : Matrix
        Pixel coordinates to page coordinates, as in ``Scene.images``.

    Returns
    -------
    BBox
        The page box of the four corners of the pixel grid.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._layers import image_matrix, pixel_box
    >>> picture = svg.Image(np.zeros((2, 4, 4)), 10, 20, 8, 4)
    >>> pixel_box(picture, image_matrix(picture))
    BBox(x=10.0, y=20.0, width=8.0, height=4.0)
    """
    from ...pathdata.data import BBox

    rows, columns = image.shape
    corners = [matrix.apply(x, y) for x in (0, columns) for y in (0, rows)]
    xs, ys = [c[0] for c in corners], [c[1] for c in corners]
    return BBox(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
