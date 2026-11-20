"""
Turning figures, ``_repr_svg_`` objects and other documents into elements for ``Document.add``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar

import numpy as np

from ..elements.base import Element
from ..elements.structure import Group
from ._constants import RASTER_REPRS

if TYPE_CHECKING:
    pass


E = TypeVar("E", bound=Element)


class SupportsSVG(Protocol):
    """Anything with a ``_repr_svg_`` (the IPython display protocol).

    Plots, diagrams and formulas from other libraries usually qualify, and can
    be passed to :meth:`Document.add`.

    See Also
    --------
    Document.add : Accepts these objects.

    Examples
    --------
    >>> import svgwriter as svg
    >>> class Dot:
    ...     def _repr_svg_(self):
    ...         return '<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>'
    >>> doc = svg.Document(10, 10)
    >>> doc.add(Dot()) is not None
    True
    >>> "<circle" in str(doc)
    True
    """

    def _repr_svg_(self) -> str | None: ...


def _ingest(item: Any) -> Any:
    """Turn anything :meth:`Document.add` accepts into an element.

    In order: elements pass through; ``__svgwriter__()`` (svgwriter's own
    protocol) is called and its result ingested; documents become a copy of
    their ``<svg>`` in a ``<g>``; numpy arrays become images; figures with
    ``savefig`` and objects with ``_repr_svg_`` become their parsed ``<svg>``
    in a ``<g>``; objects with only ``_repr_png_`` or ``_repr_jpeg_`` become an
    ``<image>``.
    """
    from ..document import Document

    if isinstance(item, Element):
        return item
    if hasattr(type(item), "__svgwriter__"):
        result = item.__svgwriter__()
        if result is None or result is item:
            raise TypeError(f"{type(item).__name__}.__svgwriter__() must return an element, document or drawable")
        return _ingest(result)
    if isinstance(item, Document):
        return _nested(item.root.clone())
    if isinstance(item, str):
        raise TypeError("add() takes elements, not strings; parse markup first: doc.add(svg.parse('<rect .../>'))")
    from ..ops.graph import draw_graph, is_graph

    if is_graph(item):
        return draw_graph(item)
    if isinstance(item, np.ndarray):
        from ..elements.structure import Image

        return Image(item)
    text = _svg_text(item)
    if text is not None:
        from ..io.parser import parse

        return _nested(parse(text))
    for name in RASTER_REPRS:
        data = getattr(item, name, lambda: None)() if hasattr(item, name) else None
        if data:
            from ..elements.structure import Image, Pixels

            pixels = Pixels.decode(data if isinstance(data, bytes) else bytes(data))
            return Image(pixels.rgba())
    return item


def _svg_text(item: Any) -> str | None:
    """SVG markup from ``savefig`` or ``_repr_svg_``, or None when the object offers neither."""
    if hasattr(item, "savefig"):
        import io

        buffer = io.BytesIO()
        item.savefig(buffer, format="svg")
        return buffer.getvalue().decode("utf-8")
    if hasattr(item, "_repr_svg_"):
        text = item._repr_svg_()
        if text:
            return str(text)
        if not any(hasattr(item, name) for name in RASTER_REPRS):
            raise TypeError(f"{type(item).__name__}._repr_svg_() returned no SVG")
    return None


def _nested(root: Element) -> Element:
    for key in ("version", "baseProfile"):
        root.attributes.pop(key, None)
    return Group(root)
