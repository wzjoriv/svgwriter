"""
Turning figures, ``_repr_svg_`` objects and other documents into elements for ``Document.add``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Protocol, TypeVar

from ..elements.base import Element
from ..elements.structure import Group

if TYPE_CHECKING:
    pass


NON_CONTENT: Final = frozenset({"defs", "style", "title", "desc", "metadata"})
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
    """Elements pass through; documents (copied) and ``_repr_svg_``/``savefig`` objects become a ``<g>`` holding an ``<svg>``."""
    from ..document import Document

    if isinstance(item, Element):
        return item
    if isinstance(item, Document):
        root = item.root.clone()
        for key in ("version", "baseProfile"):
            root.attributes.pop(key, None)
        return Group(root)
    if isinstance(item, str):
        raise TypeError("add() takes elements, not strings; parse markup first: doc.add(svg.parse('<rect .../>'))")
    if hasattr(item, "savefig"):
        import io

        buffer = io.BytesIO()
        item.savefig(buffer, format="svg")
        text = buffer.getvalue().decode("utf-8")
    elif hasattr(item, "_repr_svg_"):
        text = item._repr_svg_()
    else:
        return item
    from ..io.parser import parse

    if not text:
        raise TypeError(f"{type(item).__name__}._repr_svg_() returned no SVG")
    root = parse(text)

    for key in ("version", "baseProfile"):
        root.attributes.pop(key, None)
    return Group(root)
