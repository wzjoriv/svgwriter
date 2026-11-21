"""
Measuring a compact batch: item anchors and boxes, and the batch's bounding box, without expanding it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ..pathdata.data import BBox, PathData
from ._constants import HALF
from ._kinds import INSTANCES, TEXTS, Geometry

if TYPE_CHECKING:
    from ..elements.core import Element
    from ._kinds import Kind

__all__ = ["ItemMeasures"]


class ItemMeasures:
    """Anchors, boxes and bounds of a batch's items; mixed into :class:`~svgwriter.model.batch.Batch`."""

    __slots__ = ()

    _kind: Kind
    _count: int
    _columns: dict[str, np.ndarray] | None
    _points: np.ndarray | None
    _offsets: np.ndarray | None
    shape: Element | None

    def _shape_anchor(self) -> tuple[float, float]:
        shape = self.shape
        position = getattr(shape, "position", None)
        return (float(position.x), float(position.y)) if position is not None else (0.0, 0.0)

    def _geometry(self) -> Geometry:
        assert self._columns is not None
        return Geometry(self._columns, self._points, self._offsets)

    def _anchors(self) -> np.ndarray:
        """Each item's pivot before its transform: its box centre, a text's ``(x, y)``, an instance's shape anchor."""
        if self._kind is TEXTS:
            assert self._columns is not None
            return np.stack([self._columns["x"], self._columns["y"]], axis=1)
        if self._kind is INSTANCES:
            return np.broadcast_to(np.asarray(self._shape_anchor()), (self._count, 2))
        assert self._kind.boxes is not None
        boxes = self._kind.boxes(self._geometry())
        return np.stack([(boxes[:, 0] + boxes[:, 2]) * HALF, (boxes[:, 1] + boxes[:, 3]) * HALF], axis=1)

    def _item_boxes(self) -> np.ndarray | None:
        if self._kind.boxes is not None:
            return self._kind.boxes(self._geometry())
        shape = self.shape
        box = shape.bounds() if self._kind is INSTANCES and shape is not None else None  # type: ignore[attr-defined]
        if box is None:
            return None
        return np.broadcast_to(np.array([box.x, box.y, box.x + box.width, box.y + box.height]), (self._count, 4))

    def local_bbox(self) -> BBox | None:
        """Box around every item, each item's box carried through its own transform.

        Returns
        -------
        BBox or None
            The union, or None when empty.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.batch.circles([0, 10], [0, 5], 1).local_bbox()
        BBox(x=-1.0, y=-1.0, width=12.0, height=7.0)
        """
        if self._columns is None or self._count == 0:
            return super().local_bbox()  # type: ignore[misc, no-any-return]
        boxes = self._item_boxes()
        if boxes is None:
            return self.clone().expand().local_bbox()  # type: ignore[attr-defined, no-any-return]
        m = self._matrices()  # type: ignore[attr-defined]
        xs = np.stack([boxes[:, 0], boxes[:, 2], boxes[:, 2], boxes[:, 0]], axis=1)
        ys = np.stack([boxes[:, 1], boxes[:, 1], boxes[:, 3], boxes[:, 3]], axis=1)
        px = m[:, :1] * xs + m[:, 2:3] * ys + m[:, 4:5]
        py = m[:, 1:2] * xs + m[:, 3:4] * ys + m[:, 5:6]
        x0, y0, x1, y1 = float(px.min()), float(py.min()), float(px.max()), float(py.max())
        return BBox(x0, y0, x1 - x0, y1 - y0)

    def local_outline(self) -> PathData:
        """Union of every item's outline (measured on an expanded copy).

        Returns
        -------
        PathData
            The combined outline.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.batch.rects([0, 10], 0, 5, 5).local_outline().bbox
        BBox(x=0.0, y=0.0, width=15.0, height=5.0)
        """
        if self._columns is not None:
            return self.clone().expand().local_outline()  # type: ignore[attr-defined, no-any-return]
        return super().local_outline()  # type: ignore[misc, no-any-return]
