"""
Document size: auto-size from content, ``content_bounds`` and ``fit``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, TypeVar

from .._internal._typing import Self
from ..elements.core import Element
from ..pathdata.data import BBox

if TYPE_CHECKING:
    pass


E = TypeVar("E", bound=Element)


class Sizing:
    """Canvas sizing; mixed into :class:`~svgwriter.Document`."""

    @property
    def auto_size(self) -> bool:
        """Whether the canvas is computed from the content (no ``width``, ``height`` or ``viewBox`` set).

        Examples
        --------

        >>> from svgwriter import Document, Rect
        >>> Document().auto_size, Document(10, 10).auto_size
        (True, False)
        """
        root = self.root
        return root.get("width") is None and root.get("height") is None and root.view_box is None

    def content_bounds(self, padding: float = 0.0) -> BBox | None:
        """Union of the top-level content's stroke-inclusive bounds, grown by *padding*.

        Parameters
        ----------
        padding : float, optional
            Margin added on every side. Defaults to 0.0.

        Returns
        -------
        BBox or None
            The bounds, or None when the content has no measurable shape.

        See Also
        --------
        fit : Apply the bounds as the canvas size.

        Examples
        --------

        >>> from svgwriter import Document, Rect
        >>> doc = Document()
        >>> doc.content_bounds() is None
        True
        >>> _ = doc.rect(10, 10, 20, 20)
        >>> doc.content_bounds(padding=2)
        BBox(x=8.0, y=8.0, width=24.0, height=24.0)
        """
        box: BBox | None = None
        for element in self:
            measure = getattr(element, "render_bounds", None)
            part = measure() if measure is not None else None
            if part is not None:
                box = part if box is None else box.union(part)
        if box is None:
            return None
        return BBox(box.x - padding, box.y - padding, box.width + 2 * padding, box.height + 2 * padding)

    def fit(self, padding: float = 0.0) -> Self:
        """Set ``viewBox``, ``width`` and ``height`` to the content bounds (plus *padding*) and return ``self``.

        Parameters
        ----------
        padding : float, optional
            Margin added on every side. Defaults to 0.0.

        Returns
        -------
        Document
            This document, for chaining.

        See Also
        --------
        content_bounds : The bounds that are applied.

        Examples
        --------

        >>> from svgwriter import Document, Rect
        >>> doc = Document()
        >>> _ = doc.rect(10, 10, 20, 20)
        >>> doc.fit(padding=2).root.view_box
        ViewBox(min_x=8.0, min_y=8.0, width=24.0, height=24.0)
        """
        box = self.content_bounds(padding)
        if box is not None:
            self.root.view_box = (box.x, box.y, box.width, box.height)
            self.root.update(width=box.width, height=box.height)
        return self

    @contextmanager
    def _sized(self) -> Iterator[None]:
        if not self.auto_size:
            yield
            return
        saved = dict(self.root.attributes)
        self.fit()
        try:
            yield
        finally:
            self.root.attributes = saved
