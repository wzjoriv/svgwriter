"""
Draw ``<image>`` pixels in z-order around skia's SVG renderer, which cannot load images.
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

import numpy as np
import skia

from ..._internal._constants import CONTAINERS, VISIBLE_OVERFLOW
from ..._internal._render._layers import ancestry, drawable_order, image_matrix, image_viewport
from ..._internal._tree import clip_outline
from .._constants import CHANNEL_MAX, CONCEALED

if TYPE_CHECKING:
    from ...model.elements.core import Element
    from ...model.elements.structure import Image
    from ...model.transform.matrix import Matrix

__all__ = ["concealed", "draw_image", "hidden", "layers", "referenced", "skia_matrix"]


def layers(root: Element, atomic: Callable[[Element], bool] | None = None,
           ) -> list[tuple[list[Element], Element | None]]:
    """Split the paint order into runs of vector leaves, each followed by an image, a text or an *atomic* element.

    Skia's SVG renderer cannot load images or draw text, so each run is painted by skia and the
    embedded image or ``<text>`` (left in a render copy only to be drawn as real glyphs) that ends
    it is drawn separately, keeping z-order.

    Parameters
    ----------
    root : Element
        The tree to split.
    atomic : callable, optional
        Elements it accepts (containers included) are drawn separately, as a whole, like
        images. Defaults to None.

    Returns
    -------
    list of (list of Element, Element or None)
        Runs of vector leaves, each paired with the image or text that follows it. The last
        pair has ``None`` there.

    See Also
    --------
    svgwriter._internal._render._layers.drawable_order : The flat paint order that is split here.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops._raster._layers import layers
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 5, 5)
    >>> [(len(run), image) for run, image in layers(doc.root)]
    [(1, None)]
    """
    from ...model.elements import Image, Text

    result: list[tuple[list[Element], Element | None]] = []
    run: list[Element] = []
    for leaf in drawable_order(root, atomic):
        if isinstance(leaf, Text) or (isinstance(leaf, Image) and leaf.pixels is not None) or (
                atomic is not None and atomic(leaf)):
            result.append((run, leaf))
            run = []
        else:
            run.append(leaf)
    result.append((run, None))
    return result


def _chain(image: Element, root: Element) -> list[Element]:
    """Elements from just below *root* (or *root* itself unless it is the outer ``<svg>``) down to *image*."""
    chain: list[Element] = []
    node: Element | None = image
    while node is not None:
        if node is root and root.tag == "svg":
            break
        chain.append(node)
        if node is root:
            break
        node = node.parent
    return chain[::-1]


def skia_matrix(m: Matrix) -> skia.Matrix:
    """*m* as a ``skia.Matrix``."""
    return skia.Matrix.MakeAll(m.a, m.c, m.e, m.b, m.d, m.f, 0, 0, 1)


def referenced(element: Element, name: str) -> Element | None:
    """The element the ``url(#id)`` attribute *name* of *element* points at, or None."""
    value = element.get(name)
    target = getattr(value, "element", None)
    if target is None and value is not None and str(value).startswith("url(#"):
        target = element.root().get_element_by_id(str(value)[5:].split(")")[0])
    return target


def hidden(root: Element, keep: list[Element], atomic: Callable[[Element], bool] | None = None) -> list[Element]:
    """Leaves of *root* outside *keep*, to hide while painting one layer.

    Parameters
    ----------
    root : Element
        The tree being painted.
    keep : list of Element
        The leaves that belong to the layer being painted.
    atomic : callable, optional
        Containers it accepts count as one leaf. Defaults to None.

    Returns
    -------
    list of Element
        Every drawable leaf of *root* that is not in *keep*.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._layers import drawable_order
    >>> from svgwriter.ops._raster._layers import hidden
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 5, 5)
    >>> _ = doc.circle(5, 5, 2)
    >>> first, second = drawable_order(doc.root)
    >>> [e.tag for e in hidden(doc.root, [first])]
    ['circle']
    """
    kept = {id(e) for e in keep}
    return [leaf for leaf in drawable_order(root, atomic) if id(leaf) not in kept] + (
        [] if root.tag in CONTAINERS or id(root) in kept else [root]
    )


@contextmanager
def concealed(leaves: list[Element]) -> Generator[None, None, None]:
    """Hide *leaves* (``display="none"``, filter dropped) while the block runs, then restore them.

    The filter goes too: skia's SVG renderer still draws a filter whose result is opaque
    without input, such as lighting or a flood, for an element that is not displayed.

    Parameters
    ----------
    leaves : list of Element
        The elements to hide.

    Yields
    ------
    None
        Control while the leaves are hidden.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops._raster._layers import concealed
    >>> rect = svg.Rect(0, 0, 1, 1, filter="url(#f)")
    >>> with concealed([rect]):
    ...     rect.get("display"), rect.get("filter")
    ('none', None)
    >>> rect.get("filter")
    'url(#f)'
    """
    saved = [{name: leaf.attributes.pop(name) for name in CONCEALED if name in leaf.attributes} for leaf in leaves]
    for leaf in leaves:
        leaf.attributes[CONCEALED[0]] = "none"
    try:
        yield
    finally:
        for leaf, values in zip(leaves, saved, strict=True):
            leaf.attributes.pop(CONCEALED[0], None)
            leaf.attributes.update(values)


def draw_image(canvas: skia.Canvas, image: Image, root: Element, view: Matrix) -> None:
    """Paint *image* clipped to its viewport, with transforms, opacity, aspect ratio, clip and mask.

    Filters are applied by ``draw_filtered``, which calls this for the unfiltered picture.

    Parameters
    ----------
    canvas : skia.Canvas
        Destination canvas.
    image : Image
        An ``<image>`` element holding embedded pixels.
    root : Element
        The tree being rendered; ancestors up to *root* contribute transforms and opacity.
    view : Matrix
        Maps *root*'s parent coordinates to canvas user units (the ``viewBox`` mapping).

    See Also
    --------
    layers : Decide which images are drawn separately.
    """
    from ...model.elements import Transformable
    from .._filters import paint_mask
    from .._skia import to_skia

    _, opacity = ancestry(image, root)
    rgba = image.rgba()
    premultiplied = np.concatenate([rgba[..., :3] * rgba[..., 3:], rgba[..., 3:]], axis=-1)
    pixels = np.ascontiguousarray(np.clip(np.rint(premultiplied * CHANNEL_MAX), 0, CHANNEL_MAX).astype(np.uint8))
    picture = skia.Image.fromarray(pixels, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    canvas.save()
    canvas.concat(skia_matrix(view))
    for node in _chain(image, root):
        if isinstance(node, Transformable):
            canvas.concat(skia_matrix(node.t))
        clip = clip_outline(node)
        if clip is not None:
            canvas.clipPath(to_skia(clip), doAntiAlias=True)
    mask = referenced(image, "mask")
    canvas.saveLayer(None, skia.Paint())
    m = image_matrix(image)
    canvas.save()
    box = image_viewport(image)
    if box is not None and str(image.get("overflow", "hidden")) not in VISIBLE_OVERFLOW:
        canvas.clipRect(skia.Rect.MakeXYWH(box.x, box.y, box.width, box.height), doAntiAlias=True)
    canvas.concat(skia.Matrix.MakeAll(m.a, m.c, m.e, m.b, m.d, m.f, 0, 0, 1))
    paint = skia.Paint(AntiAlias=True)
    paint.setAlphaf(opacity)
    canvas.drawImage(picture, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), paint)
    canvas.restore()
    if mask is not None:
        from ._canvas import paint_svg

        paint_mask(canvas, mask, paint_svg)
    canvas.restore()
    canvas.restore()
