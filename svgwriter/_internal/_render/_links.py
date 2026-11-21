"""
Linked images made drawable: local files, SVG documents and ``data:`` URIs embedded as pixels.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .._constants import (
    BASE64_SUFFIX,
    DATA_URI,
    GZIP_MAGIC,
    LINK_CACHE,
    LINKED_OVERSAMPLE,
    PERCENT,
    SVG_DATA_URI,
    VIEWPORT_AXES,
)
from ._layers import ancestry, viewport_extent

if TYPE_CHECKING:
    from ...document import Document
    from ...elements.core import Element

__all__ = ["base_uri", "resolve_links"]


def base_uri(element: Element) -> str:
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
def _load(path: str, mtime: float, width: float, height: float, ratio: str, density: float) -> Any:
    from ...elements.structure import Pixels

    if path.lower().endswith((".svg", ".svgz")):
        from ...export import load

        _LOADING.add(path)
        try:
            return _rasterized(load(path), width, height, ratio, density)
        finally:
            _LOADING.discard(path)
    return Pixels.decode(Path(path).read_bytes())


def _rasterized(document: Document, width: float, height: float, ratio: str, density: float) -> Any:
    """The pixels of a linked SVG *document* drawn into its *width* by *height* ``<image>`` viewport.

    The image's ``preserveAspectRatio`` (*ratio*, when set) replaces the document's own; a
    document without a ``viewBox`` is drawn unscaled and clipped to the viewport. *density* is
    pixels per user unit.
    """
    from ...elements.structure import Pixels

    root = document.root
    if root.get("viewBox") is None:
        root.attributes["viewBox"] = f"0 0 {width} {height}"
    if ratio:
        root.attributes["preserveAspectRatio"] = ratio
    root.attributes["width"], root.attributes["height"] = width, height
    columns, rows = max(1, round(width * density)), max(1, round(height * density))
    return Pixels.from_array(document.rasterize(size=(columns, rows)))


def _density(image: Element) -> float:
    """Pixels per user unit to rasterize a linked SVG at: its scale on the page, oversampled."""
    import math

    scale = math.sqrt(abs(ancestry(image, image.root())[0].determinant))
    return max(1.0, scale) * LINKED_OVERSAMPLE


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
    """Embed the pixels of ``<image>`` and ``<feImage>`` elements that link to local files.

    Works in place, so call it on a render copy. Relative links resolve against the document's
    source path and ``xml:base``. Remote URLs are not fetched; unreadable files, and links
    back to a document already being drawn (a cycle), are left as links and not drawn.

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
    >>> from svgwriter._internal._render._links import resolve_links
    >>> doc = svg.Document(10, 10)
    >>> resolve_links(doc.root)
    """
    from urllib.parse import unquote, urljoin, urlparse
    from urllib.request import url2pathname

    from ...document import Document
    from ...elements.structure import Image, Pixels

    effects = [e for e in root.iter() if e.tag == "feImage" and isinstance(e.attributes.get("xlink:href"), str)
               and not str(e.attributes["xlink:href"]).startswith("#")]
    for image in [e for e in root.iter() if isinstance(e, Image)] + effects:
        if isinstance(image, Image):
            _absolute_geometry(image)
        data = _svg_data(str(image.attributes.get("xlink:href", "")))
        if data is not None:
            try:
                image.attributes["xlink:href"] = _rasterized(Document.from_string(data), _length(image.get("width")),
                                                             _length(image.get("height")), _ratio(image),
                                                             _density(image))
            except ValueError:
                image.attributes.pop("xlink:href")
    for effect in effects:
        href = effect.attributes.get("xlink:href")
        if isinstance(href, str) and href.startswith(DATA_URI):
            effect.attributes["xlink:href"] = Pixels(None, source=href)
    source = getattr(root.root(), "_source_path", None)
    own = str(Path(source).resolve()) if source else None
    entered = own is not None and own not in _LOADING
    if entered:
        _LOADING.add(own)
    try:
        for image in [e for e in root.iter() if isinstance(e, Image) and e.pixels is None] + effects:
            href = image.attributes.get("xlink:href")
            if not isinstance(href, str):
                continue
            target = urlparse(urljoin(base_uri(image), str(href)))
            if target.scheme != "file":
                continue
            path = str(Path(url2pathname(unquote(target.path))).resolve())
            if path in _LOADING:
                continue
            try:
                pixels = _load(path, Path(path).stat().st_mtime, _length(image.get("width")),
                               _length(image.get("height")), _ratio(image), _density(image))
            except (OSError, ValueError):
                continue
            image.attributes["xlink:href"] = pixels
    finally:
        if entered:
            _LOADING.discard(own)


def _absolute_geometry(image: Element) -> None:
    """Rewrite percentage ``x``/``y``/``width``/``height`` of *image* as user units of its viewport."""
    from ...attributes.length import Length, Unit

    extent = None
    for name, axis in VIEWPORT_AXES.items():
        value = image.attributes.get(name)
        if value is None:
            continue
        length = Length.parse(value)
        if length.unit is Unit.PERCENT:
            extent = extent or viewport_extent(image)
            image.attributes[name] = length.value * extent[axis] / PERCENT


def _ratio(image: Element) -> str:
    value = image.get("preserveAspectRatio")
    return "" if value is None else str(value.svg_value() if hasattr(value, "svg_value") else value)


def _length(value: object) -> float:
    from ...attributes.length import Length

    try:
        return Length.parse(value).to_user_units() if value is not None else 0.0
    except ValueError:
        return 0.0
