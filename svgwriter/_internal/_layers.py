"""
Paint order, linked-image loading and image placement shared by the renderer and the exporters.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._constants import (
    BASE64_SUFFIX,
    CONTAINERS,
    GZIP_MAGIC,
    LINK_CACHE,
    NOT_RENDERED,
    PERCENT,
    SVG_DATA_URI,
    VIEWPORT_AXES,
    VIEWPORT_FALLBACK,
)

if TYPE_CHECKING:
    from ..attributes.viewbox import PreserveAspectRatio
    from ..document import Document
    from ..elements.core import Element
    from ..elements.structure import Image
    from ..pathdata.data import BBox
    from ..transform.matrix import Matrix

__all__ = ["ancestry", "drawable_order", "fit_box", "image_matrix", "pixel_box", "resolve_links", "viewport_extent"]


def drawable_order(root: Element) -> list[Element]:
    """Rendered leaf elements in paint order (containers and definitions skipped).

    Walks the tree depth first, descending into ``svg``, ``g``, ``a`` and ``switch`` and
    skipping definition-only elements such as ``defs``, ``clipPath`` and gradients.

    Parameters
    ----------
    root : Element
        The element whose descendants are listed.

    Returns
    -------
    list of Element
        Leaf elements, first painted first.

    See Also
    --------
    svgwriter.ops._layers.layers : Group the same leaves into runs around embedded images.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._layers import drawable_order
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
            if child.tag in CONTAINERS:
                visit(child)
            else:
                order.append(child)

    if root.tag in CONTAINERS:
        visit(root)
    elif root.tag not in NOT_RENDERED:
        order.append(root)
    return order


def _base_uri(element: Element) -> str:
    """The URI that relative references inside *element* resolve against (``xml:base`` honoured)."""
    import os
    from urllib.parse import urljoin

    chain = []
    node: Element | None = element
    while node is not None:
        chain.append(node)
        node = node.parent
    source = getattr(chain[-1], "_source_path", None)
    base = Path(source).resolve().as_uri() if source else Path(os.getcwd()).resolve().as_uri() + "/"
    for node in reversed(chain):
        extra = node.attributes.get("xml:base")
        if extra:
            base = urljoin(base, str(extra))
    return base


_LOADING: set[str] = set()


@lru_cache(maxsize=LINK_CACHE)
def _load(path: str, mtime: float, width: float, height: float) -> Any:
    from ..elements.structure import Pixels

    if path.lower().endswith((".svg", ".svgz")):
        from ..export import load

        if path in _LOADING:
            raise ValueError(f"{path} links back to itself")
        _LOADING.add(path)
        try:
            return _rasterized(load(path), width, height)
        finally:
            _LOADING.discard(path)
    return Pixels.decode(Path(path).read_bytes())


def _rasterized(document: Document, width: float, height: float) -> Any:
    """The pixels of a linked SVG *document* drawn into its *width* by *height* ``<image>`` viewport."""
    from ..elements.structure import Pixels

    columns, rows = max(1, round(width)), max(1, round(height))
    for name, size in (("width", columns), ("height", rows)):
        if "%" in str(document.root.get(name, "%")):
            document.root.attributes[name] = size
    return Pixels.from_array(document.rasterize(size=(columns, rows)))


def _svg_data(uri: str) -> bytes | None:
    """The (gunzipped) bytes of an SVG ``data:`` URI, or None for any other link."""
    import base64
    import gzip
    from urllib.parse import unquote_to_bytes

    header, _, payload = uri.partition(",")
    if not header.lower().startswith(SVG_DATA_URI):
        return None
    data = base64.b64decode(payload) if header.lower().endswith(BASE64_SUFFIX) else unquote_to_bytes(payload)
    return gzip.decompress(data) if data[:len(GZIP_MAGIC)] == GZIP_MAGIC else data


def resolve_links(root: Element) -> None:
    """Embed the pixels of ``<image>`` elements that link to local files.

    Works in place, so call it on a render copy. Relative links resolve against the document's
    source path and ``xml:base``. Remote URLs are not fetched; unreadable files are left as
    links and not drawn.

    Parameters
    ----------
    root : Element
        The tree whose ``<image>`` elements are resolved.

    See Also
    --------
    svgwriter.ops._layers.layers : Split a resolved tree into vector runs and embedded images.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._layers import resolve_links
    >>> doc = svg.Document(10, 10)
    >>> resolve_links(doc.root)
    """
    from urllib.parse import unquote, urljoin, urlparse
    from urllib.request import url2pathname

    from ..document import Document
    from ..elements.structure import Image

    for image in [e for e in root.iter() if isinstance(e, Image)]:
        _absolute_geometry(image)
        data = _svg_data(str(image.attributes.get("xlink:href", "")))
        if data is not None:
            try:
                image.attributes["xlink:href"] = _rasterized(Document.from_string(data), _length(image.get("width")),
                                                             _length(image.get("height")))
            except ValueError:
                image.attributes.pop("xlink:href")
    for image in [e for e in root.iter() if isinstance(e, Image) and e.pixels is None]:
        href = image.attributes.get("xlink:href")
        if href is None:
            continue
        target = urlparse(urljoin(_base_uri(image), str(href)))
        if target.scheme != "file":
            continue
        path = url2pathname(unquote(target.path))
        try:
            pixels = _load(path, Path(path).stat().st_mtime, _length(image.get("width")), _length(image.get("height")))
        except (OSError, ValueError):
            continue
        image.attributes["xlink:href"] = pixels


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
    >>> from svgwriter._internal._layers import viewport_extent
    >>> doc = svg.Document(40, 30)
    >>> viewport_extent(doc.rect(0, 0, 1, 1))
    (40.0, 30.0)
    """
    from ..attributes.length import Length, Unit
    from ..attributes.viewbox import ViewBox

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


def _absolute_geometry(image: Element) -> None:
    """Rewrite percentage ``x``/``y``/``width``/``height`` of *image* as user units of its viewport."""
    from ..attributes.length import Length, Unit

    extent = None
    for name, axis in VIEWPORT_AXES.items():
        value = image.attributes.get(name)
        if value is None:
            continue
        length = Length.parse(value)
        if length.unit is Unit.PERCENT:
            extent = extent or viewport_extent(image)
            image.attributes[name] = length.value * extent[axis] / PERCENT


def _length(value: object) -> float:
    from ..attributes.length import Length

    try:
        return Length.parse(value).to_user_units() if value is not None else 0.0
    except ValueError:
        return 0.0


def _number(value: object, default: float = 0.0) -> float:
    from ..attributes.length import Length

    return default if value is None else Length.parse(value).to_user_units()


def fit_box(box_w: float, box_h: float, w: float, h: float, ratio: PreserveAspectRatio) -> Matrix:
    """Map a *w* by *h* area into a *box_w* by *box_h* box as ``preserveAspectRatio`` *ratio* says."""
    from ..attributes.viewbox import Align, MeetOrSlice
    from ..transform.matrix import Matrix

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
    >>> from svgwriter._internal._layers import image_matrix
    >>> picture = svg.Image(np.zeros((2, 2, 4)), 10, 20, 4, 4)
    >>> (image_matrix(picture).e, image_matrix(picture).f)
    (10.0, 20.0)
    """
    from ..attributes.viewbox import PreserveAspectRatio
    from ..transform.matrix import Matrix

    rows, columns = image.shape
    ratio_text = image.get("preserveAspectRatio")
    ratio = ratio_text if isinstance(ratio_text, PreserveAspectRatio) else (
        PreserveAspectRatio.parse(str(ratio_text)) if ratio_text is not None else PreserveAspectRatio()
    )
    fit = fit_box(_number(image.get("width"), columns), _number(image.get("height"), rows), columns, rows, ratio)
    return Matrix.translate(_number(image.get("x")), _number(image.get("y"))) @ fit


def ancestry(element: Element, root: Element) -> tuple[Matrix, float]:
    """The transform and opacity *element* collects from itself up to *root* (an outer ``<svg>`` root excluded)."""
    from ..elements import Transformable
    from ..transform.matrix import IDENTITY

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
    >>> from svgwriter._internal._layers import image_matrix, pixel_box
    >>> picture = svg.Image(np.zeros((2, 4, 4)), 10, 20, 8, 4)
    >>> pixel_box(picture, image_matrix(picture))
    BBox(x=10.0, y=20.0, width=8.0, height=4.0)
    """
    from ..pathdata.data import BBox

    rows, columns = image.shape
    corners = [matrix.apply(x, y) for x in (0, columns) for y in (0, rows)]
    xs, ys = [c[0] for c in corners], [c[1] for c in corners]
    return BBox(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
