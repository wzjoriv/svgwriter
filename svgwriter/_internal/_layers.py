"""
Paint order, linked-image loading and image placement shared by the renderer and the exporters.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._constants import CONTAINERS, LINK_CACHE, NOT_RENDERED

if TYPE_CHECKING:
    from ..attributes.viewbox import PreserveAspectRatio
    from ..elements.core import Element
    from ..elements.structure import Image
    from ..transform.matrix import Matrix

__all__ = ["ancestry", "drawable_order", "fit_box", "image_matrix", "resolve_links"]


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


@lru_cache(maxsize=LINK_CACHE)
def _load(path: str, mtime: float, width: float, height: float) -> Any:
    from ..elements.structure import Pixels

    if path.lower().endswith((".svg", ".svgz")):
        from ..export import load

        document = load(path)
        columns, rows = max(1, round(width)), max(1, round(height))
        return Pixels.from_array(document.rasterize(size=(columns, rows)))
    return Pixels.decode(Path(path).read_bytes())


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

    from ..elements.structure import Image

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
