"""
Inkscape connectors: paths that stay attached to two objects (``inkscape:connection-start/end``).
"""

from __future__ import annotations

from typing import NamedTuple

from ..._internal._tree import resolve
from ...model.elements.core import Element
from ...model.pathdata.builder import PathBuilder
from ._constants import (
    CONNECTION_END,
    CONNECTION_START,
    CONNECTOR_CURVATURE,
    CONNECTOR_TYPE,
    CONNECTOR_TYPES,
    DEFAULT_CONNECTOR,
)

__all__ = ["Connection", "connect", "connection"]


class Connection(NamedTuple):
    """The objects a connector joins; either end may be None when it is loose.

    Attributes
    ----------
    start, end : Element or None
        The objects at each end.

    Examples
    --------
    >>> from svgwriter.formats.inkscape import Connection
    >>> Connection(None, None).start is None
    True
    """

    start: Element | None
    end: Element | None


def connection(path: Element) -> Connection | None:
    """The objects joined by an Inkscape connector, or None when *path* is not one.

    Parameters
    ----------
    path : Element
        Usually a ``<path>`` read from an Inkscape file.

    Returns
    -------
    Connection or None
        The start and end objects, found by id in the path's document.

    Examples
    --------
    >>> import svgwriter as svg
    >>> a, b = svg.rect(0, 0, 10, 10, id="a"), svg.rect(50, 0, 10, 10, id="b")
    >>> line = svg.Path()
    >>> root = svg.svg(a, b, line)
    >>> svg.inkscape.connect(line, a, b)
    >>> svg.inkscape.connection(line).end is b
    True
    """
    if CONNECTOR_TYPE not in path.attributes:
        return None
    return Connection(resolve(path, path.attributes.get(CONNECTION_START)), resolve(path, path.attributes.get(CONNECTION_END)))


def connect(path: Element, start: Element | None, end: Element | None, *, kind: str = DEFAULT_CONNECTOR) -> None:
    """Make *path* an Inkscape connector from *start* to *end*.

    Both ends receive an id if they have none. When both ends have known
    bounds, the path is redrawn as a straight line between their centres;
    Inkscape reroutes it around obstacles when the file is edited there.

    Parameters
    ----------
    path : Element
        A ``<path>``.
    start, end : Element or None
        The objects to join; None leaves that end loose, and None for both
        turns the path back into a plain path.
    kind : {"polyline", "orthogonal"}, optional
        Inkscape's routing style. Defaults to ``"polyline"``.

    Raises
    ------
    ValueError
        If `kind` is unknown.

    Examples
    --------
    >>> import svgwriter as svg
    >>> a, b = svg.circle(0, 0, 5, id="a"), svg.circle(40, 0, 5, id="b")
    >>> line = svg.Path(stroke="black")
    >>> root = svg.svg(a, b, line)
    >>> svg.inkscape.connect(line, a, b)
    >>> str(line.d), line.attributes["inkscape:connection-end"]
    ('M0 0 L40 0', '#b')
    """
    if start is None and end is None:
        for name in (CONNECTOR_TYPE, CONNECTOR_CURVATURE, CONNECTION_START, CONNECTION_END):
            path.attributes.pop(name, None)
        return
    if kind not in CONNECTOR_TYPES:
        raise ValueError(f"unknown connector type {kind!r}; choose one of {', '.join(CONNECTOR_TYPES)}")
    path.attributes.update({CONNECTOR_TYPE: kind, CONNECTOR_CURVATURE: 0})
    for name, target in ((CONNECTION_START, start), (CONNECTION_END, end)):
        if target is None:
            path.attributes.pop(name, None)
        else:
            path.attributes[name] = f"#{target.ensure_id()}"
    boxes = [getattr(target, "bounds", lambda: None)() for target in (start, end)]
    if boxes[0] is not None and boxes[1] is not None and hasattr(path, "d"):
        (x1, y1), (x2, y2) = boxes[0].center, boxes[1].center
        path.d = PathBuilder().move_to(x1, y1).line_to(x2, y2).build()  # type: ignore[attr-defined]
