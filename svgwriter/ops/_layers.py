"""
Draw ``<image>`` pixels in z-order around skia's SVG renderer, which cannot load images.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import skia

from .._internal._constants import CONTAINERS
from .._internal._layers import ancestry, drawable_order, image_matrix
from .._internal._tree import clip_outline
from ._constants import CHANNEL_MAX

if TYPE_CHECKING:
    from ..elements.core import Element
    from ..elements.structure import Image
    from ..transform.matrix import Matrix

__all__ = ["draw_image", "hidden", "layers"]


def layers(root: Element) -> list[tuple[list[Element], Element | None]]:
    """Split the paint order into runs of vector leaves, each followed by an image or a text.

    Skia's SVG renderer cannot load images or draw text, so each run is painted by skia and the
    embedded image or ``<text>`` (left in a render copy only to be drawn as real glyphs) that ends
    it is drawn separately, keeping z-order.

    Parameters
    ----------
    root : Element
        The tree to split.

    Returns
    -------
    list of (list of Element, Element or None)
        Runs of vector leaves, each paired with the image or text that follows it. The last
        pair has ``None`` there.

    See Also
    --------
    svgwriter._internal._layers.drawable_order : The flat paint order that is split here.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops._layers import layers
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 5, 5)
    >>> [(len(run), image) for run, image in layers(doc.root)]
    [(1, None)]
    """
    from ..elements import Image, Text

    result: list[tuple[list[Element], Element | None]] = []
    run: list[Element] = []
    for leaf in drawable_order(root):
        if isinstance(leaf, Text) or (isinstance(leaf, Image) and leaf.pixels is not None):
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


def _skia_matrix(m: Matrix) -> skia.Matrix:
    return skia.Matrix.MakeAll(m.a, m.c, m.e, m.b, m.d, m.f, 0, 0, 1)


def _referenced(element: Element, name: str) -> Element | None:
    """The element a ``url(#id)`` attribute points at, or None."""
    value = element.get(name)
    target = getattr(value, "element", None)
    if target is None and value is not None and str(value).startswith("url(#"):
        target = element.root().get_element_by_id(str(value)[5:].split(")")[0])
    return target


def hidden(root: Element, keep: list[Element]) -> list[Element]:
    """Leaves of *root* outside *keep*, to hide while painting one layer.

    Parameters
    ----------
    root : Element
        The tree being painted.
    keep : list of Element
        The leaves that belong to the layer being painted.

    Returns
    -------
    list of Element
        Every drawable leaf of *root* that is not in *keep*.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._layers import drawable_order
    >>> from svgwriter.ops._layers import hidden
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 5, 5)
    >>> _ = doc.circle(5, 5, 2)
    >>> first, second = drawable_order(doc.root)
    >>> [e.tag for e in hidden(doc.root, [first])]
    ['circle']
    """
    kept = {id(e) for e in keep}
    return [leaf for leaf in drawable_order(root) if id(leaf) not in kept] + (
        [] if root.tag in CONTAINERS or id(root) in kept else [root]
    )


def draw_image(canvas: skia.Canvas, image: Image, root: Element, view: Matrix) -> None:
    """Paint *image* with its transforms, opacity, aspect ratio and clip.

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
    from ..elements import Transformable
    from ._image_effects import image_filter, paint_mask
    from ._skia import to_skia

    _, opacity = ancestry(image, root)
    pixels = np.ascontiguousarray(np.clip(np.rint(image.rgba() * CHANNEL_MAX), 0, CHANNEL_MAX).astype(np.uint8))
    picture = skia.Image.fromarray(pixels, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    canvas.save()
    canvas.concat(_skia_matrix(view))
    for node in _chain(image, root):
        if isinstance(node, Transformable):
            canvas.concat(_skia_matrix(node.t))
        clip = clip_outline(node)
        if clip is not None:
            canvas.clipPath(to_skia(clip), doAntiAlias=True)
    effects, mask = _referenced(image, "filter"), _referenced(image, "mask")
    layer = skia.Paint()
    if effects is not None:
        layer.setImageFilter(image_filter(effects))
    canvas.saveLayer(None, layer)
    m = image_matrix(image)
    canvas.save()
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
