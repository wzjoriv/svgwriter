"""
Element-tree helpers shared across packages: references, clip outlines, replacement and insertion cursors.
"""

from __future__ import annotations

import weakref
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from ._typing import Stack

if TYPE_CHECKING:
    from ..elements.core import Element
    from ..pathdata.data import PathData

__all__ = ["attach_cursor", "clip_outline", "cursor_of", "element_list", "replace_in_parent", "resolve", "settle_parent"]


def resolve(element: Element, value: Any) -> Element | None:
    """The element an attribute value refers to, if it can be found.

    Parameters
    ----------
    element : Element
        The element holding the value; its root is searched for ids.
    value : object
        A reference, ``#id``, ``url(#id)`` text, or None.

    Returns
    -------
    Element or None
        The referenced element, or None.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._tree import resolve
    >>> g = svg.group(svg.circle(0, 0, 1, id="dot"))
    >>> resolve(g, "url(#dot)").tag
    'circle'
    """
    from ..elements.core import Element

    target = getattr(value, "element", None)
    root = element.root()
    if isinstance(target, Element) and target.root() is root:
        return target
    if value is None:
        return None
    text = str(value.svg_value() if hasattr(value, "svg_value") else value).strip()
    if text.startswith("url(") and text.endswith(")"):
        text = text[4:-1].strip("'\" ")
    found = root.get_element_by_id(text[1:]) if text.startswith("#") else None
    return found if found is not None or not isinstance(target, Element) else target


def clip_outline(element: Element) -> PathData | None:
    """The clip region of *element* in its local coordinates, or ``None``.

    Parameters
    ----------
    element : Element
        The clipped element.

    Returns
    -------
    PathData or None
        The clip outline, or None when the element is not clipped.

    Raises
    ------
    TypeError
        If ``clip-path`` refers to something other than a ``<clipPath>``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._tree import clip_outline
    >>> clip_outline(svg.rect(0, 0, 9, 9)) is None
    True
    """
    from ..elements import PathOperand
    from ..pathdata.data import PathData
    from ..transform.matrix import Matrix

    clip = resolve(element, element.attributes.get("clip-path"))
    if clip is None:
        return None
    if not isinstance(clip, PathOperand):
        raise TypeError(f"clip-path refers to <{clip.tag}>, not a <clipPath>")
    data = clip.outline()
    if str(clip.get("clipPathUnits", "userSpaceOnUse")) == "objectBoundingBox":
        box = element.local_outline().bbox if isinstance(element, PathOperand) else None
        if box is None:
            return PathData()
        data = data.transformed(Matrix(box.width, 0, 0, box.height, box.x, box.y))
    return data


def replace_in_parent(old: Element, new: Element) -> None:
    """Swap *new* into *old*'s place in its parent; an explicit (not generated) id moves with it.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> c = doc.circle(5, 5, 5, id="dot")
    >>> c -= svg.rect(0, 0, 5, 5)
    >>> [(e.tag, e.id) for e in doc]
    [('path', 'dot')]
    """
    parent = old.parent
    if parent is None or new is old:
        return
    index = next(i for i, child in enumerate(parent) if child is old)
    explicit = None if old._auto_id else old.get("id")
    parent.remove(old)
    if explicit is not None:
        old.discard("id")
        new.id = explicit
    parent.insert(index, new)


_CURSORS: weakref.WeakKeyDictionary[Element, Stack[Element]] = weakref.WeakKeyDictionary()


def attach_cursor(element: Element, stack: Stack[Element] | None) -> None:
    """Let ``with element:`` move *stack*'s insertion point.

    Parameters
    ----------
    element : Element
        The element used in a ``with`` statement.
    stack : Stack of Element or None
        The insertion stack to move; None does nothing.

    See Also
    --------
    cursor_of : Look up the stack attached to an element.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._stack import Stack
    >>> from svgwriter._internal._tree import attach_cursor, cursor_of
    >>> group, stack = svg.group(), Stack()
    >>> attach_cursor(group, stack)
    >>> cursor_of(group) is stack
    True
    """
    if stack is not None:
        _CURSORS[element] = stack


def cursor_of(element: Element) -> Stack[Element] | None:
    """Return the insertion stack attached to *element*, if any.

    Parameters
    ----------
    element : Element
        The element to look up.

    Returns
    -------
    Stack of Element or None
        The stack set by :func:`attach_cursor`, or None.

    See Also
    --------
    attach_cursor : Attach an insertion stack to an element.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._tree import cursor_of
    >>> cursor_of(svg.group()) is None
    True
    """
    return _CURSORS.get(element)


def element_list(items: Element | str | Iterable[Element]) -> list[Element | str]:
    """One element, a text run or an iterable of elements, as a list.

    Parameters
    ----------
    items : Element, str or iterable of Element
        What to normalize.

    Returns
    -------
    list
        The items as a list.

    Raises
    ------
    TypeError
        If *items* is not an element, a string or an iterable of elements.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._tree import element_list
    >>> len(element_list([svg.circle(0, 0, 1), svg.circle(1, 1, 1)]))
    2
    """
    from ..elements.core import Element

    if isinstance(items, (Element, str)):
        return [items]
    try:
        flat = list(items)
    except TypeError:
        raise TypeError(f"expected an element or an iterable of elements, got {type(items).__name__}") from None
    for item in flat:
        if not isinstance(item, Element):
            raise TypeError(f"expected elements, got {type(item).__name__}")
    return flat  # type: ignore[return-value]


def settle_parent(element: Element) -> None:
    """Let the layout group holding *element* place its children, so its geometry is current.

    Parameters
    ----------
    element : Element
        Any element; nothing happens unless its parent is a layout group.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._tree import settle_parent
    >>> a, b = svg.rect(0, 0, 4, 4), svg.rect(0, 0, 4, 4)
    >>> _ = svg.HStack(a, b, gap=1)
    >>> settle_parent(b)
    >>> b.t.apply(0, 0)
    Point(x=5.0, y=0.0)
    """
    parent = element.parent
    if parent is not None and parent.arranges_children:
        parent.arrange()  # type: ignore[attr-defined]
