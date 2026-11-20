"""
Flatten a document into filled and stroked paths in page coordinates for simple vector formats.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..attributes.cascade import computed
from ..attributes.length import Length
from ..color.color import Color
from ..pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo
from ..pathdata.data import PathData
from ._constants import DEFAULT_MITER, NONE
from ._paints import _paint, _shading
from ._patterns import _ancestry, _expand_patterns

if TYPE_CHECKING:
    from ..document import Document
    from ..elements.core._element import Element
    from ._paints import Shading

__all__ = ["Item", "Scene", "flatten", "to_cubic"]


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
    shading: Shading | None = None


@dataclass
class Scene:
    """The flattened page: size in user units and its items in paint order.

    Attributes
    ----------
    width, height : float
        Page size in user units.
    items : list of Item
        Painted paths, first painted first.
    texts : list of TextRun
        Text runs when flattening with ``text=True``; empty otherwise.
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
    texts: list[Any] = field(default_factory=list)


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


def _number(element: Element, name: str, default: float, rules: list) -> float:
    value = computed(element, name, default, rules)
    try:
        return float(Length.parse(value).to_user_units())
    except (TypeError, ValueError):
        return default


def _hidden(leaf: Element, root: Element) -> bool:
    node: Element | None = leaf
    while node is not None and node is not root:
        if str(node.get("display", "")) == NONE:
            return True
        node = node.parent
    return str(computed(leaf, "visibility", "visible")) in ("hidden", "collapse")


def flatten(document: Document, *, handled: frozenset[str] = frozenset(), text: bool = False) -> Scene:
    """Reduce *document* to :class:`Item` paths in its user space (``viewBox`` applied).

    Parameters
    ----------
    document : Document
        The document to flatten.
    text : bool, optional
        Leave ``<text>`` out of the outlines and return it as :attr:`Scene.texts`
        runs, for formats that write real text. Defaults to False.
    handled : frozenset of str, optional
        Tags the caller draws itself (``{"image"}`` for formats that embed
        pictures), left out of the warning. Defaults to an empty set.

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
    from ..elements._behavior._geometry import PathOperand
    from ..ops._layers import drawable_order
    from ..ops._renderable import renderable_copy
    from ..ops.render import _view, document_size

    with document._sized():
        width, height = document_size(document)
        view = _view(document, width, height)
        source = document.root
        if text:
            source = source.clone()
            for element in [e for e in source.iter() if e.tag == "text"]:
                if element.parent is not None:
                    element.parent.remove(element)
        root = renderable_copy(source)
        _expand_patterns(root)
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
            shading=_shading(leaf, matrix @ leaf.t, rules),
        ))
    reported = [entry for entry in skipped if entry.strip("<>") not in handled]
    if reported:
        warnings.warn(f"not representable in this format, skipped: {', '.join(sorted(set(reported)))}",
                      stacklevel=3)
    texts = []
    if text:
        from ._text_runs import text_runs

        texts = text_runs(document)
    return Scene(width, height, items, skipped, texts)
