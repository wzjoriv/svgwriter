"""Draw ``<image>`` pixels in z-order around skia's SVG renderer, which cannot load images."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import numpy as np
import skia

from ..attributes.length import Length
from ..attributes.viewbox import Align, MeetOrSlice, PreserveAspectRatio
from ..transform.matrix import IDENTITY, Matrix

if TYPE_CHECKING:
    from ..elements.base import Element
    from ..elements.structure import Image

__all__ = ["draw_image", "drawable_order", "hidden", "image_matrix", "layers"]

NOT_RENDERED: Final = frozenset({"defs", "clipPath", "mask", "pattern", "marker", "symbol", "linearGradient",
                                 "radialGradient", "filter", "title", "desc", "metadata", "style", "font",
                                 "font-face", "glyph", "missing-glyph"})
CONTAINERS: Final = frozenset({"svg", "g", "a", "switch"})
CHANNEL_MAX: Final = 255
LINK_CACHE: Final = 64


def drawable_order(root: Element) -> list[Element]:
    """Rendered leaf elements in paint order (containers and definitions skipped)."""
    order: list[Element] = []

    def visit(node: Element) -> None:
        for child in node:
            if child.tag in NOT_RENDERED:
                continue
            if child.tag in CONTAINERS:
                visit(child)
            else:
                order.append(child)

    visit(root)
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
    """Embed the pixels of ``<image>`` elements that link to local files (in place, on a render copy).

    Remote URLs are not fetched; unreadable files are left as links and not drawn.
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
    try:
        return Length.parse(value).to_user_units() if value is not None else 0.0
    except ValueError:
        return 0.0


def layers(root: Element) -> list[tuple[list[Element], Image | None]]:
    """Split the paint order into runs of vector leaves, each followed by an embedded image."""
    from ..elements.structure import Image

    result: list[tuple[list[Element], Image | None]] = []
    run: list[Element] = []
    for leaf in drawable_order(root):
        if isinstance(leaf, Image) and leaf.pixels is not None:
            result.append((run, leaf))
            run = []
        else:
            run.append(leaf)
    result.append((run, None))
    return result


def _number(value: object, default: float = 0.0) -> float:
    return default if value is None else Length.parse(value).to_user_units()


def _fit(box_w: float, box_h: float, w: float, h: float, ratio: PreserveAspectRatio) -> Matrix:
    sx, sy = box_w / w, box_h / h
    if ratio.align is Align.NONE:
        return Matrix.scale(sx, sy)
    s = max(sx, sy) if ratio.meet_or_slice is MeetOrSlice.SLICE else min(sx, sy)
    name = ratio.align.value
    fx = {"xMin": 0.0, "xMid": 0.5, "xMax": 1.0}[name[:4]]
    fy = {"YMin": 0.0, "YMid": 0.5, "YMax": 1.0}[name[4:]]
    return Matrix.translate((box_w - w * s) * fx, (box_h - h * s) * fy) @ Matrix.scale(s)


def image_matrix(image: Image) -> Matrix:
    """Map pixel coordinates of *image* to its parent's user space (``t`` excluded)."""
    rows, columns = image.shape
    ratio_text = image.get("preserveAspectRatio")
    ratio = ratio_text if isinstance(ratio_text, PreserveAspectRatio) else (
        PreserveAspectRatio.parse(str(ratio_text)) if ratio_text is not None else PreserveAspectRatio()
    )
    fit = _fit(_number(image.get("width"), columns), _number(image.get("height"), rows), columns, rows, ratio)
    return Matrix.translate(_number(image.get("x")), _number(image.get("y"))) @ fit


def _ancestry(image: Element, root: Element) -> tuple[Matrix, float]:
    from ..elements._transformable import Transformable

    matrix, opacity = IDENTITY, 1.0
    node: Element | None = image
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


def hidden(root: Element, keep: list[Element]) -> list[Element]:
    """Leaves of *root* outside *keep*, to hide while painting one layer."""
    kept = {id(e) for e in keep}
    return [leaf for leaf in drawable_order(root) if id(leaf) not in kept] + (
        [] if root.tag in CONTAINERS or id(root) in kept else [root]
    )


def draw_image(canvas: skia.Canvas, image: Image, root: Element, view: Matrix) -> None:
    """Paint *image* with its transforms, opacity, aspect ratio and clip."""
    from ..elements._geometry import clip_outline
    from ._skia import to_skia

    ancestry, opacity = _ancestry(image, root)
    pixels = np.ascontiguousarray(np.clip(np.rint(image.rgba() * CHANNEL_MAX), 0, CHANNEL_MAX).astype(np.uint8))
    picture = skia.Image.fromarray(pixels, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    canvas.save()
    to_parent = view @ ancestry
    canvas.concat(skia.Matrix.MakeAll(to_parent.a, to_parent.c, to_parent.e, to_parent.b, to_parent.d, to_parent.f,
                                      0, 0, 1))
    clip = clip_outline(image)
    if clip is not None:
        canvas.clipPath(to_skia(clip), doAntiAlias=True)
    m = image_matrix(image)
    canvas.concat(skia.Matrix.MakeAll(m.a, m.c, m.e, m.b, m.d, m.f, 0, 0, 1))
    paint = skia.Paint(AntiAlias=True)
    paint.setAlphaf(opacity)
    canvas.drawImage(picture, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), paint)
    canvas.restore()
