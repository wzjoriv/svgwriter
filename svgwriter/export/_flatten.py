"""
Flatten a document into filled and stroked paths in page coordinates for simple vector formats.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from ..attributes.cascade import computed
from ..attributes.length import Length
from ..color.color import Color, as_color
from ..pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo
from ..pathdata.data import PathData
from ..transform.matrix import IDENTITY, Matrix

if TYPE_CHECKING:
    from ..document import Document
    from ..elements.base import Element

__all__ = ["Item", "Scene", "flatten", "to_cubic"]

NONE: Final = "none"
DEFAULT_MITER: Final = 4.0


@dataclass
class Item:
    """One painted path: geometry in page units plus solid paints.

    Attributes
    ----------
    data : PathData
        Outline in page coordinates.
    fill, stroke : Color or None
        Solid paints; None means no paint.
    fill_opacity, stroke_opacity : float
        Opacity of each paint, group opacity included.
    evenodd : bool
        Whether the fill uses the even-odd rule.
    stroke_width : float
        Stroke width in page units.
    linecap, linejoin : str
        ``stroke-linecap`` and ``stroke-linejoin`` values.
    miter_limit : float
        ``stroke-miterlimit``.
    dashes : tuple of float
        Dash lengths in page units; empty for a solid stroke.

    See Also
    --------
    flatten : Produce items from a document.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._flatten import flatten
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> item = flatten(doc).items[0]
    >>> item.fill.hex, item.stroke
    ('#ff0000', None)
    """

    data: PathData
    fill: Color | None
    fill_opacity: float
    evenodd: bool
    stroke: Color | None
    stroke_opacity: float
    stroke_width: float
    linecap: str
    linejoin: str
    miter_limit: float
    dashes: tuple[float, ...]


@dataclass
class Scene:
    """The flattened page: size in user units and its items in paint order.

    Attributes
    ----------
    width, height : float
        Page size in user units.
    items : list of Item
        Painted paths, first painted first.
    skipped : list of str
        Descriptions of elements that could not be represented.

    See Also
    --------
    flatten : Produce a scene from a document.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._flatten import flatten
    >>> scene = flatten(svg.Document(10, 5))
    >>> (scene.width, scene.height, scene.items)
    (10.0, 5.0, [])
    """

    width: float
    height: float
    items: list[Item]
    skipped: list[str]


def to_cubic(data: PathData) -> list[tuple[str, tuple[float, ...]]]:
    """``M``/``L``/``C``/``Z`` operations (quadratics and arcs converted) for PostScript-like targets.

    Parameters
    ----------
    data : PathData
        The outline to convert.

    Returns
    -------
    list of (str, tuple of float)
        Each operation letter with its absolute coordinates.

    See Also
    --------
    flatten : Build the items whose data this converts.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._flatten import to_cubic
    >>> to_cubic(svg.PathData("M0 0 L10 0 Z"))
    [('M', (0.0, 0.0)), ('L', (10.0, 0.0)), ('Z', ())]
    """
    from ..ops._skia import from_skia, to_skia

    ops: list[tuple[str, tuple[float, ...]]] = []
    current = (0.0, 0.0)
    for command in from_skia(to_skia(data)):
        if isinstance(command, MoveTo):
            current = (command.x, command.y)
            ops.append(("M", current))
        elif isinstance(command, LineTo):
            current = (command.x, command.y)
            ops.append(("L", current))
        elif isinstance(command, QuadTo):
            (x0, y0), (qx, qy), (x, y) = current, (command.x1, command.y1), (command.x, command.y)
            ops.append(("C", (x0 + 2 / 3 * (qx - x0), y0 + 2 / 3 * (qy - y0),
                              x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y), x, y)))
            current = (x, y)
        elif isinstance(command, CurveTo):
            ops.append(("C", (command.x1, command.y1, command.x2, command.y2, command.x, command.y)))
            current = (command.x, command.y)
        elif isinstance(command, ClosePath):
            ops.append(("Z", ()))
    return ops


def _paint(element: Element, name: str, default: str, rules: list) -> Color | None:
    from ..elements._geometry import resolve

    value = computed(element, name, default, rules)
    text = str(value.svg_value() if hasattr(value, "svg_value") else value).strip()
    if text == NONE:
        return None
    if text == "currentColor":
        text = str(computed(element, "color", "black", rules))
    if text.startswith("url("):
        server = resolve(element, value)
        stops = list(server.iter("stop")) if server is not None else []
        fallback = text.split(")", 1)[1].strip()
        if stops:
            return as_color(str(computed(stops[0], "stop-color", "black", rules)))
        return as_color(fallback) if fallback and fallback != NONE else None
    try:
        return as_color(value if isinstance(value, Color) else text)
    except (TypeError, ValueError):
        return None


def _number(element: Element, name: str, default: float, rules: list) -> float:
    value = computed(element, name, default, rules)
    try:
        return float(Length.parse(value).to_user_units())
    except (TypeError, ValueError):
        return default


def _ancestry(leaf: Element, root: Element) -> tuple[Matrix, float]:
    from ..elements._transformable import Transformable

    matrix, opacity = IDENTITY, 1.0
    node = leaf.parent
    while node is not None and node is not root:
        if isinstance(node, Transformable):
            matrix = node.t @ matrix
        opacity *= float(node.get("opacity", 1.0))
        node = node.parent
    return matrix, opacity


def _hidden(leaf: Element, root: Element) -> bool:
    node: Element | None = leaf
    while node is not None and node is not root:
        if str(node.get("display", "")) == NONE:
            return True
        node = node.parent
    return str(computed(leaf, "visibility", "visible")) in ("hidden", "collapse")


def flatten(document: Document) -> Scene:
    """Reduce *document* to :class:`Item` paths in its user space (``viewBox`` applied).

    Parameters
    ----------
    document : Document
        The document to flatten.

    Returns
    -------
    Scene
        The page size and the painted paths.

    Warns
    -----
    UserWarning
        When elements cannot be represented and are skipped.

    See Also
    --------
    to_cubic : Convert an item's outline for PostScript-like targets.

    Notes
    -----
    Gradients and patterns become their first stop color; images, masks,
    filters and markers are not represented and are listed in ``skipped``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._flatten import flatten
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> scene = flatten(doc)
    >>> len(scene.items), scene.skipped
    (1, [])
    """
    from ..attributes.cascade import rules_of
    from ..elements._geometry import PathOperand
    from ..ops._layers import drawable_order
    from ..ops.render import _view, document_size, renderable_copy

    with document._sized():
        width, height = document_size(document)
        view = _view(document, width, height)
        root = renderable_copy(document.root)
    rules = rules_of(root)
    items: list[Item] = []
    skipped: list[str] = []
    for leaf in drawable_order(root):
        if _hidden(leaf, root):
            continue
        if not isinstance(leaf, PathOperand):
            skipped.append(f"<{leaf.tag}>")
            continue
        try:
            outline = leaf.outline()
        except TypeError as exc:
            skipped.append(str(exc))
            continue
        ancestry, opacity = _ancestry(leaf, root)
        matrix = view @ ancestry
        opacity *= float(leaf.get("opacity", 1.0))
        stretch = math.sqrt(abs((matrix @ leaf.t).determinant)) or 1.0
        dashes = computed(leaf, "stroke-dasharray", NONE, rules)
        items.append(Item(
            data=outline.transformed(matrix),
            fill=_paint(leaf, "fill", "black", rules),
            fill_opacity=opacity * _number(leaf, "fill-opacity", 1.0, rules),
            evenodd=str(computed(leaf, "fill-rule", "nonzero", rules)) == "evenodd",
            stroke=_paint(leaf, "stroke", NONE, rules),
            stroke_opacity=opacity * _number(leaf, "stroke-opacity", 1.0, rules),
            stroke_width=_number(leaf, "stroke-width", 1.0, rules) * stretch,
            linecap=str(computed(leaf, "stroke-linecap", "butt", rules)),
            linejoin=str(computed(leaf, "stroke-linejoin", "miter", rules)),
            miter_limit=_number(leaf, "stroke-miterlimit", DEFAULT_MITER, rules),
            dashes=() if str(dashes) == NONE else tuple(
                v * stretch for v in (float(p) for p in str(dashes).replace(",", " ").split())),
        ))
    if skipped:
        warnings.warn(f"not representable in this format, skipped: {', '.join(sorted(set(skipped)))}",
                      stacklevel=3)
    return Scene(width, height, items, skipped)
