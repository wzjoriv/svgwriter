"""
Making batches: circles, dots, rects, lines, polylines, texts and instances of any element.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ..attributes.names import KNOWN_ATTRIBUTES, svg_name
from ._batch import Batch
from ._columns import broadcast, frozen
from ._constants import DEFAULT_DOT_SIZE, HALF, IDENTITY_ROW
from ._kinds import CIRCLES, INSTANCES, LINES, POLYGONS, POLYLINES, RECTS, TEXTS
from ._transforms import compose

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

    from ..elements.core import Element

__all__ = ["circles", "instances", "lines", "points", "polylines", "rects", "texts"]


def _attributes(given: dict[str, Any], **named: Any) -> dict[str, Any]:
    for key in given:
        if svg_name(key) not in KNOWN_ATTRIBUTES:
            raise TypeError(f"unknown attribute keyword {key!r} for a batch")
    return {**named, **given}


def circles(cx: ArrayLike, cy: ArrayLike, r: ArrayLike = 1.0, *, fill: Any = None, stroke: Any = None,
            opacity: ArrayLike | None = None, **attributes: Any) -> Batch:
    """Many circles at once; every argument is a scalar or an array, broadcast with numpy rules.

    Parameters
    ----------
    cx, cy : float or array_like
        Centres.
    r : float or array_like, optional
        Radii. Defaults to 1.
    fill, stroke : paint, list of colours or array, optional
        One paint for all, a list of colours, an ``(N, 3|4)`` RGB(A) array (``0..1`` floats or
        ``0..255`` integers; alpha becomes ``fill-opacity``) or a :func:`colormap`. Default to None.
    opacity : float or array_like, optional
        Opacity of each item. Defaults to None.
    **attributes
        Any other SVG attribute in Python spelling, shared or one value per item.

    Returns
    -------
    Batch
        A compact batch of ``<circle>`` items.

    Raises
    ------
    ValueError
        If the arguments do not broadcast together.
    TypeError
        If a keyword is not an SVG attribute.

    See Also
    --------
    points : Dots of a given size.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> x, y = np.meshgrid(np.arange(4) * 10, np.arange(3) * 10)
    >>> grid = svg.batch.circles(x, y, 2, fill=svg.batch.colormap("viridis", x + y))
    >>> len(grid), grid.column("fill")[0]
    (12, '#440154')
    """
    columns = broadcast({"cx": cx, "cy": cy, "r": r}, _attributes(attributes, fill=fill, stroke=stroke,
                                                                     opacity=opacity))
    return Batch._create(CIRCLES, columns)


def points(x: ArrayLike, y: ArrayLike, size: ArrayLike = DEFAULT_DOT_SIZE, *, fill: Any = None,
           opacity: ArrayLike | None = None, **attributes: Any) -> Batch:
    """Dots: circles of diameter *size* at ``(x, y)``, for scatter plots and particles.

    Parameters
    ----------
    x, y : float or array_like
        Positions.
    size : float or array_like, optional
        Diameters. Defaults to 2.
    fill : paint, list of colours or array, optional
        As for :func:`circles`. Defaults to None.
    opacity : float or array_like, optional
        Opacity of each dot. Defaults to None.
    **attributes
        Any other SVG attribute in Python spelling.

    Returns
    -------
    Batch
        A compact batch of ``<circle>`` items.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.batch.points([0, 5], [1, 2], 3).item_markup()
    ['<circle cx="0" cy="1" r="1.5"/>', '<circle cx="5" cy="2" r="1.5"/>']
    """
    return circles(x, y, np.asarray(size, dtype=float) * HALF, fill=fill, opacity=opacity, **attributes)


def rects(x: ArrayLike, y: ArrayLike, width: ArrayLike, height: ArrayLike, *, rx: ArrayLike | None = None,
          ry: ArrayLike | None = None, fill: Any = None, stroke: Any = None, opacity: ArrayLike | None = None,
          **attributes: Any) -> Batch:
    """Many rectangles at once, broadcast as in :func:`circles`.

    Parameters
    ----------
    x, y : float or array_like
        Top-left corners.
    width, height : float or array_like
        Sizes.
    rx, ry : float or array_like, optional
        Corner radii. Default to None.
    fill, stroke : paint, list of colours or array, optional
        As for :func:`circles`. Default to None.
    opacity : float or array_like, optional
        Opacity of each item. Defaults to None.
    **attributes
        Any other SVG attribute in Python spelling.

    Returns
    -------
    Batch
        A compact batch of ``<rect>`` items.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> heights = np.array([3, 7, 5])
    >>> bars = svg.batch.rects(np.arange(3) * 6, 10 - heights, 5, heights, fill="slateblue")
    >>> bars.bounds()
    BBox(x=0.0, y=3.0, width=17.0, height=7.0)
    """
    geometry = {"x": x, "y": y, "width": width, "height": height}
    geometry.update({name: value for name, value in (("rx", rx), ("ry", ry)) if value is not None})
    columns = broadcast(geometry, _attributes(attributes, fill=fill, stroke=stroke, opacity=opacity))
    return Batch._create(RECTS, columns)


def lines(x1: ArrayLike, y1: ArrayLike, x2: ArrayLike, y2: ArrayLike, *, stroke: Any = None,
          opacity: ArrayLike | None = None, **attributes: Any) -> Batch:
    """Many line segments at once, broadcast as in :func:`circles`.

    Parameters
    ----------
    x1, y1, x2, y2 : float or array_like
        End points.
    stroke : paint, list of colours or array, optional
        As for :func:`circles`. Defaults to None.
    opacity : float or array_like, optional
        Opacity of each item. Defaults to None.
    **attributes
        Any other SVG attribute in Python spelling (``stroke_width`` arrays included).

    Returns
    -------
    Batch
        A compact batch of ``<line>`` items.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> angles = np.linspace(0, np.pi, 5)
    >>> rays = svg.batch.lines(0, 0, 10 * np.cos(angles), 10 * np.sin(angles), stroke="black")
    >>> len(rays)
    5
    """
    columns = broadcast({"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                        _attributes(attributes, stroke=stroke, opacity=opacity))
    return Batch._create(LINES, columns)


def polylines(points: Any, *, closed: bool = False, fill: Any = None, stroke: Any = None,
              opacity: ArrayLike | None = None, **attributes: Any) -> Batch:
    """Many polylines (or, *closed*, polygons) with any number of vertices each.

    Parameters
    ----------
    points : array_like or sequence of array_like
        An ``(N, K, 2)`` array, or a list of ``(K_i, 2)`` vertex arrays of different lengths.
    closed : bool, optional
        Make ``<polygon>`` items. Defaults to False.
    fill, stroke : paint, list of colours or array, optional
        As for :func:`circles`. Default to None.
    opacity : float or array_like, optional
        Opacity of each item. Defaults to None.
    **attributes
        Any other SVG attribute in Python spelling, shared or one value per item.

    Returns
    -------
    Batch
        A compact batch of ``<polyline>`` or ``<polygon>`` items.

    Raises
    ------
    ValueError
        If an item has no vertices or a vertex is not an ``(x, y)`` pair.

    Examples
    --------
    >>> import svgwriter as svg
    >>> marks = svg.batch.polylines([[(0, 0), (5, 5)], [(0, 5), (2, 0), (4, 5)]], stroke="black", fill="none")
    >>> marks.item_markup()
    ['<polyline points="0,0 5,5"/>', '<polyline points="0,5 2,0 4,5"/>']
    """
    vertices = [np.asarray(item, dtype=float).reshape(-1, 2) for item in points]
    if any(len(item) == 0 for item in vertices):
        raise ValueError("every polyline needs at least one vertex")
    counts = np.array([len(item) for item in vertices], dtype=np.int64)
    offsets = frozen(np.concatenate([[0], np.cumsum(counts)]))
    flat = frozen(np.concatenate(vertices) if vertices else np.zeros((0, 2)))
    columns = broadcast({}, _attributes(attributes, fill=fill, stroke=stroke, opacity=opacity), count=len(vertices))
    return Batch._create(POLYGONS if closed else POLYLINES, columns, points=flat, offsets=offsets)


def texts(text: Any, x: ArrayLike, y: ArrayLike, *, fill: Any = None, opacity: ArrayLike | None = None,
          **attributes: Any) -> Batch:
    """Many short texts at once, broadcast as in :func:`circles` (the strings too).

    Parameters
    ----------
    text : str or sequence of str
        The texts.
    x, y : float or array_like
        Positions of each text's anchor point on its baseline.
    fill : paint, list of colours or array, optional
        As for :func:`circles`. Defaults to None.
    opacity : float or array_like, optional
        Opacity of each item. Defaults to None.
    **attributes
        Any other SVG attribute in Python spelling (``font_size``, ``text_anchor``...).

    Returns
    -------
    Batch
        A compact batch of ``<text>`` items.

    Examples
    --------
    >>> import svgwriter as svg
    >>> labels = svg.batch.texts(["a", "b<c"], [0, 20], 10, font_size=8)
    >>> print(labels.to_string(pretty=False, xml_declaration=False))
    <g font-size="8"><text x="0" y="10">a</text><text x="20" y="10">b&lt;c</text></g>
    """
    strings = np.asarray(text, dtype=object)
    columns = broadcast({"x": x, "y": y}, _attributes(attributes, fill=fill, opacity=opacity),
                        shapes=(strings.shape,))
    content = frozen(np.broadcast_to(strings, columns.shape).reshape(columns.count).astype(str).astype(object))
    return Batch._create(TEXTS, columns, content=content)


def instances(shape: Element, x: ArrayLike, y: ArrayLike, *, angle: ArrayLike = 0.0, scale: ArrayLike = 1.0,
              fill: Any = None, opacity: ArrayLike | None = None, **attributes: Any) -> Batch:
    """Copies of any element, each placed, turned and scaled on its own, written as ``<use>``.

    The element is copied once into the batch's ``<defs>``; each instance puts the element's
    anchor (its centre unless set) at ``(x, y)``.

    Parameters
    ----------
    shape : Element
        What to repeat: a shape, a group, a text...
    x, y : float or array_like
        Where each copy's anchor goes.
    angle : float or array_like, optional
        Rotation of each copy in degrees, clockwise on screen. Defaults to 0.
    scale : float or array_like, optional
        Uniform scale of each copy. Defaults to 1.
    fill : paint, list of colours or array, optional
        As for :func:`circles`; it shows where the shape leaves ``fill`` unset. Defaults to None.
    opacity : float or array_like, optional
        Opacity of each copy. Defaults to None.
    **attributes
        Any other SVG attribute in Python spelling.

    Returns
    -------
    Batch
        A compact batch of ``<use>`` items.

    Examples
    --------
    >>> import svgwriter as svg
    >>> arrow = svg.polygon([(0, -2), (6, 0), (0, 2)])
    >>> field = svg.batch.instances(arrow, [10, 30], 10, angle=[0, 90], fill=["red", "blue"])
    >>> field.item_markup()[1]
    '<use fill="#0000ff" transform="matrix(0 1 -1 0 30 7)" xlink:href="#polygon1"/>'
    """
    columns = broadcast({"x": x, "y": y, "angle": angle, "scale": scale},
                        _attributes(attributes, fill=fill, opacity=opacity))
    px, py, degrees, factor = (columns.items.pop(name) for name in ("x", "y", "angle", "scale"))
    copy = shape.clone()
    copy.attributes.pop("id", None)
    copy.ensure_id()
    batch = Batch._create(INSTANCES, columns, shape=copy)
    ax, ay = batch._shape_anchor()
    radians = np.radians(degrees)
    cos, sin = np.cos(radians) * factor, np.sin(radians) * factor
    placed = np.stack([cos, sin, -sin, cos, px, py], axis=1)
    to_origin = np.tile(IDENTITY_ROW, (columns.count, 1))
    to_origin[:, 4], to_origin[:, 5] = -ax, -ay
    batch._matrix = frozen(compose(placed, to_origin))
    return batch
