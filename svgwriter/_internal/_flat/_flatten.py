"""
Flatten a document into filled and stroked paths in page coordinates for simple vector formats.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .._constants import DEFAULT_MITER, DROPPED_EFFECTS, MAX_SEGMENTS, NONE
from ._paints import _paint, _shading
from ._patterns import _ancestry, _expand_patterns

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ...document import Document
    from ...model.color.color import Color
    from ...model.elements.core import Element
    from ...model.pathdata.data import PathData
    from ._paints import Shading

__all__ = ["Item", "Point", "Scene", "flatten", "polylines", "to_cubic"]

Point = tuple[float, float]


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
    shading : Shading or None
        The gradient behind the fill, for formats that can write gradients.
    link : str or None
        The ``href`` of the nearest enclosing ``<a>``, for formats that keep links.
    source : Element or None
        The element painted, in the flattening's copy of the tree (its
        ancestors and attributes intact), for formats that keep animation.

    See Also
    --------
    flatten : Produce items from a document.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._flat._flatten import flatten
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
    link: str | None = None
    source: Element | None = field(default=None, compare=False, repr=False)


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
    images : list of (int, Image, Matrix)
        With ``"image"`` in ``handled``: each embedded image, the number of items painted before it and
        the matrix from its pixel grid to the page, in paint order.

    See Also
    --------
    flatten : Produce a scene from a document.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._flat._flatten import flatten
    >>> scene = flatten(svg.Document(10, 5))
    >>> (scene.width, scene.height, scene.items)
    (10.0, 5.0, [])
    """

    width: float
    height: float
    items: list[Item]
    skipped: list[str]
    texts: list[Any] = field(default_factory=list)
    images: list[tuple[int, Any, Any]] = field(default_factory=list)

    def painted(self) -> Iterator[Item | tuple[Any, Any]]:
        """Items and ``(image, matrix)`` pairs in paint order."""
        pending = iter(self.images)
        image = next(pending, None)
        for index, item in enumerate([*self.items, None]):
            while image is not None and image[0] <= index:
                yield image[1], image[2]
                image = next(pending, None)
            if item is not None:
                yield item


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
    >>> from svgwriter._internal._flat._flatten import to_cubic
    >>> to_cubic(svg.PathData("M0 0 L10 0 Z"))
    [('M', (0.0, 0.0)), ('L', (10.0, 0.0)), ('Z', ())]
    """
    from ...model.pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo
    from ...ops import from_skia, to_skia

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
    from ...model.attributes.cascade import computed
    from ...model.units.length import Length

    value = computed(element, name, default, rules)
    try:
        return float(Length.parse(value).to_user_units())
    except (TypeError, ValueError):
        return default


def _hidden(leaf: Element, root: Element) -> bool:
    from ...model.attributes.cascade import computed

    node: Element | None = leaf
    while node is not None and node is not root:
        if str(node.get("display", "")) == NONE:
            return True
        node = node.parent
    return str(computed(leaf, "visibility", "visible")) in ("hidden", "collapse")


def _effects_and_link(leaf: Element, root: Element) -> tuple[list[str], str | None]:
    """The masks, filters and markers on *leaf* or its ancestors (dropped by flattening) and its link."""
    dropped: list[str] = []
    link: str | None = None
    node: Element | None = leaf
    while node is not None and node is not root:
        dropped += [name for name, attributes in DROPPED_EFFECTS.items() if any(node.get(a) for a in attributes)]
        if link is None and node.tag == "a":
            link = str(node.get("href") or node.get("xlink:href") or "") or None
        node = node.parent
    return dropped, link


def flatten(document: Document, *, handled: frozenset[str] = frozenset(), text: bool = False,
            color_glyphs: bool = True) -> Scene:
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
    color_glyphs : bool, optional
        Leave emoji to the outlines or text runs, warning when outlines lose them (colour
        glyphs have no outline); False when the caller places them itself, see
        :func:`~svgwriter._internal._typography._emoji.color_glyph_images`. Defaults to True.

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
    Gradients become their average color along the axis (with the gradient kept in
    :attr:`Item.shading`), patterns are expanded into their tiles and markers
    into shapes; images, masks and filters are not represented and are listed in ``skipped``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._flat._flatten import flatten
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> scene = flatten(doc)
    >>> len(scene.items), scene.skipped
    (1, [])
    """
    from ...model.attributes.cascade import computed
    from ...model.attributes.rules import rules_of
    from ...model.elements import Image, PathOperand
    from ...ops.render import page_size
    from .._render._layers import ancestry, drawable_order, image_matrix
    from .._render._rendering import renderable_copy, view_matrix

    with document._prepared():
        width, height = page_size(document)
        view = view_matrix(document, width, height)
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
    images: list[tuple[int, Any, Any]] = []
    for leaf in drawable_order(root):
        if _hidden(leaf, root):
            continue
        if isinstance(leaf, Image) and "image" in handled:
            if leaf.pixels is not None:
                images.append((len(items), leaf, view @ ancestry(leaf, root)[0] @ image_matrix(leaf)))
            continue
        if not isinstance(leaf, PathOperand):
            skipped.append(f"<{leaf.tag}>")
            continue
        try:
            outline = leaf.outline()
        except TypeError as exc:
            skipped.append(str(exc))
            continue
        inherited, opacity = _ancestry(leaf, root)
        dropped, link = _effects_and_link(leaf, root)
        skipped += dropped
        matrix = view @ inherited
        opacity *= float(leaf.get("opacity", 1.0))
        stretch = math.sqrt(abs((matrix @ leaf.matrix).determinant)) or 1.0
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
            shading=_shading(leaf, matrix @ leaf.matrix, rules),
            link=link,
            source=leaf,
        ))
    if color_glyphs and not text and _has_emoji(document):
        skipped.append("colour emoji")
    reported = [entry for entry in skipped if entry.strip("<>") not in handled]
    if reported:
        warnings.warn(f"not representable in this format, skipped: {', '.join(sorted(set(reported)))}",
                      stacklevel=3)
    texts = []
    if text:
        from ._text_runs import text_runs

        texts = text_runs(document, color_glyphs=color_glyphs)
    return Scene(width, height, items, skipped, texts, images)


def _has_emoji(document: Document) -> bool:
    from .._typography._emoji import color_glyph_boxes

    return next(color_glyph_boxes(document), None) is not None


def polylines(data: object, tolerance: float) -> list[tuple[list[Point], bool]]:
    """Subpaths as point lists (curves subdivided to within *tolerance*), each with a closed flag.

    Parameters
    ----------
    data : PathData
        The outline to flatten.
    tolerance : float
        Maximum deviation allowed when curves become line segments, in the data's units.

    Returns
    -------
    list of (list of (float, float), bool)
        One entry per subpath: its points and whether it was closed. Closed subpaths repeat
        their first point at the end.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._flat._flatten import polylines
    >>> polylines(svg.PathData("M0 0 L10 0 L10 10 Z"), 0.1)
    [([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 0.0)], True)]
    """
    result: list[tuple[list[Point], bool]] = []
    points: list[Point] = []
    current: Point = (0.0, 0.0)
    for op, args in to_cubic(data):  # type: ignore[arg-type]
        if op == "M":
            if len(points) > 1:
                result.append((points, False))
            current = (args[0], args[1])
            points = [current]
        elif op == "L":
            current = (args[0], args[1])
            points.append(current)
        elif op == "C":
            p0, p1, p2, p3 = current, (args[0], args[1]), (args[2], args[3]), (args[4], args[5])
            dd = max(math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1]),
                     math.hypot(p1[0] - 2 * p2[0] + p3[0], p1[1] - 2 * p2[1] + p3[1]))
            steps = min(MAX_SEGMENTS, max(1, math.ceil(math.sqrt(0.75 * dd / tolerance)))) if tolerance > 0 else 1
            for i in range(1, steps + 1):
                t = i / steps
                u = 1 - t
                points.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                               u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
            current = p3
        elif op == "Z" and points:
            if points[-1] != points[0]:
                points.append(points[0])
            result.append((points, True))
            current = points[0]
            points = [current]
    if len(points) > 1:
        result.append((points, False))
    return result
