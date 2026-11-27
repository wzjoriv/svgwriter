"""
``<use>`` instances expanded into copies of what they reference, for a render copy.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from .._constants import (
    EXTERNAL_ID_PREFIX,
    LINK_CACHE,
    PERCENT,
    URL_REFERENCE_RE,
    USE_GEOMETRY,
    USE_NESTING,
    VISIBLE_OVERFLOW,
)

if TYPE_CHECKING:
    from ...model.elements.core import Element

__all__ = ["expand_uses"]


def expand_uses(root: Element) -> None:
    """Replace each ``<use>`` by a ``<g>`` holding a copy of its target, as SVG's instance tree says.

    The group keeps the ``<use>``'s presentation attributes, so the copy inherits from it, and
    carries its transform followed by the ``x``/``y`` offset. A ``<symbol>`` (or nested ``<svg>``)
    target is fitted into the ``<use>``'s ``width`` and ``height`` through its ``viewBox`` and
    clipped to that viewport unless its ``overflow`` is visible. Uses whose references form a cycle
    are removed, as SVG makes them errors; uses that cannot be resolved are left alone. An
    instance from another file brings copies of the resources it references there.

    Parameters
    ----------
    root : Element
        A render copy with styles already resolved; it is changed in place.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._instances import expand_uses
    >>> doc = svg.Document(20, 20)
    >>> dot = doc.define(svg.circle(0, 0, 2, id="dot"))
    >>> _ = doc.add(svg.Use(dot, x=5, fill="red"))
    >>> copy = doc.root.clone()
    >>> expand_uses(copy)
    >>> [(e.tag, [c.tag for c in e]) for e in copy if e.tag != "defs"]
    [('g', ['circle'])]
    """
    from ...model.elements.structure import Use

    for use in _cyclic([e for e in root.iter() if isinstance(e, Use)]):
        if use.parent is not None:
            use.parent.remove(use)
    serial = 0
    for _ in range(USE_NESTING):
        expanded = False
        for use in [e for e in root.iter() if isinstance(e, Use)]:
            target = use.referenced() or _external(use)
            if target is None or use.parent is None:
                continue
            serial += 1
            _replace(use, target, root, serial)
            expanded = True
        if not expanded:
            return


def _cyclic(uses: list[Element]) -> list[Element]:
    """The uses whose references lead back to themselves, which SVG treats as errors and does not render."""
    from ...model.elements.structure import Use

    targets = {id(use): use.referenced() for use in uses}
    state: dict[int, bool] = {}

    def loops(use: Element, path: set[int]) -> bool:
        if id(use) in state:
            return state[id(use)]
        target = targets.get(id(use))
        if target is None:
            return False
        if id(use) in path or _encloses(target, use):
            return True
        path.add(id(use))
        found = any(loops(inner, path) for inner in target.iter() if isinstance(inner, Use))
        path.discard(id(use))
        state[id(use)] = found
        return found

    return [use for use in uses if loops(use, set())]


def _external(use: Element) -> Element | None:
    """The element a ``<use>`` links to in another local SVG file, with that file's styles resolved."""
    from urllib.parse import unquote, urldefrag, urljoin, urlparse
    from urllib.request import url2pathname

    from ._links import base_uri

    href = use.attributes.get("xlink:href", use.attributes.get("href"))
    if href is None or str(href).startswith("#"):
        return None
    address, fragment = urldefrag(urljoin(base_uri(use), str(href)))
    target = urlparse(address)
    if target.scheme != "file" or not fragment:
        return None
    path = Path(url2pathname(unquote(target.path)))
    try:
        document = _document(str(path), path.stat().st_mtime)
    except (OSError, ValueError):
        return None
    return document.get_element_by_id(fragment) if document is not None else None


@lru_cache(maxsize=LINK_CACHE)
def _document(path: str, mtime: float) -> Element | None:
    from ...document import Document
    from ...model.attributes.cascade import resolve_styles

    root = Document.open(path).root
    resolve_styles(root)
    return root


def _encloses(target: Element, use: Element) -> bool:
    node: Element | None = use
    while node is not None:
        if node is target:
            return True
        node = node.parent
    return False


def _replace(use: Element, target: Element, root: Element, serial: int) -> None:
    from ...model.elements import Group
    from ...model.transform.matrix import Matrix
    from .._tree import replace_in_parent
    from ._layers import _number

    group = Group()
    group.attributes.update((k, v) for k, v in use.attributes.items() if k not in USE_GEOMETRY)
    group.matrix = use.matrix @ Matrix.translate(_number(use.get("x")), _number(use.get("y")))  # type: ignore[attr-defined]
    if target.tag in ("symbol", "svg"):
        for part in _viewport(use, target, root, serial):
            group.add(part)
    else:
        group.add(_instance(target))
    source = target.root()
    if source is not root.root():
        resources = _imported([child for child in group if not isinstance(child, str)], source, serial)
        if resources is not None:
            group.insert(0, resources)
    replace_in_parent(use, group)


def _imported(instances: list[Element], source: Element, serial: int) -> Element | None:
    """Copies of what *instances* reference in their own (external) document, renamed, in a ``<defs>``.

    References inside *instances* and inside the copied resources are rewritten to the new ids,
    so an external gradient, pattern, clip path, mask, filter or marker keeps its meaning.
    """
    from ...model.elements import Defs

    prefix = f"{EXTERNAL_ID_PREFIX}{serial}-"
    taken: dict[str, Element] = {}
    pending = list(instances)
    while pending:
        for element in list(pending.pop().iter()):
            for name, value in list(element.attributes.items()):
                text = str(value.svg_value() if hasattr(value, "svg_value") else value)
                names = URL_REFERENCE_RE.findall(text)
                if name == "xlink:href" and text.startswith("#"):
                    names.append(text[1:])
                for reference in names:
                    if reference not in taken:
                        found = source.get_element_by_id(reference)
                        if found is None:
                            continue
                        taken[reference] = found.clone()
                        taken[reference].attributes["id"] = prefix + reference
                        pending.append(taken[reference])
                    text = text.replace(f"#{reference}", f"#{prefix}{reference}")
                    element.attributes[name] = text
    return Defs(*taken.values()) if taken else None


def _instance(target: Element) -> Element:
    copy = target.clone()
    for element in copy.iter():
        element.attributes.pop("id", None)
    return copy


def _viewport(use: Element, target: Element, root: Element, serial: int) -> list[Element]:
    """The children of a ``<symbol>`` or ``<svg>`` fitted into the ``<use>``'s viewport, clipped when overflow hides."""
    from ...model.attributes.viewbox import PreserveAspectRatio, ViewBox
    from ...model.elements import ClipPath, Group, Rect
    from ...model.transform.matrix import IDENTITY, Matrix
    from ._layers import fit_box

    view = root.get("viewBox")
    view = view if isinstance(view, ViewBox) or view is None else ViewBox.parse(str(view))
    width = _size(use, target, "width", view.width if view else 0.0)
    height = _size(use, target, "height", view.height if view else 0.0)
    box = target.get("viewBox")
    box = box if isinstance(box, ViewBox) or box is None else ViewBox.parse(str(box))
    matrix = IDENTITY
    if box is not None and box.width and box.height and width and height:
        ratio = target.get("preserveAspectRatio")
        ratio = ratio if isinstance(ratio, PreserveAspectRatio) else (
            PreserveAspectRatio.parse(str(ratio)) if ratio is not None else PreserveAspectRatio())
        matrix = fit_box(width, height, box.width, box.height, ratio) @ Matrix.translate(-box.min_x, -box.min_y)
    content = Group(*(_instance(child) for child in target if not isinstance(child, str)))
    content.attributes.update((k, v) for k, v in target.attributes.items()
                              if k not in USE_GEOMETRY and k not in ("viewBox", "preserveAspectRatio", "overflow"))
    content.matrix = matrix  # type: ignore[attr-defined]
    holder = Group(content)
    if target.tag == "svg":
        holder.attributes["transform"] = (f"translate({_size(use, target, 'x', view.width if view else 0.0, own=True)} "
                                          f"{_size(use, target, 'y', view.height if view else 0.0, own=True)})")
    if str(target.get("overflow", "hidden")) in VISIBLE_OVERFLOW or not (width and height):
        return [holder]
    clip = ClipPath(Rect(0, 0, width, height), id=f"svgwriter-use-viewport-{serial}")
    holder.attributes["clip-path"] = f"url(#{clip.id})"
    return [clip, holder]


def _size(use: Element, target: Element, name: str, viewport: float, *, own: bool = False) -> float:
    """A ``<use>`` viewport length, the ``<use>``'s value winning unless *own* asks for the target's."""
    from ...model.units.lengths import Length, Unit

    value = None if own else use.get(name)
    value = target.get(name) if value is None else value
    if value is None:
        return viewport
    length = Length.parse(value)
    return length.value * viewport / PERCENT if length.unit is Unit.PERCENT else length.to_user_units()
