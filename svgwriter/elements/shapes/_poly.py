"""``polyline`` and ``polygon``."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, ClassVar, Final

import numpy as np

from ..._internal._constants import DEFAULT_PRECISION
from ..._internal._numbers import format_number
from ..._internal._typing import Self
from ...path.builder import PathBuilder
from ...path.data import BBox, PathData
from ._base import Shape, parse_points

PointsLike = np.ndarray | Sequence[Sequence[float]]
_EMPTY: Final = np.zeros((0, 2))
_EMPTY.flags.writeable = False


class PointList:
    """Immutable ``points`` attribute value wrapping an ``(N, 2)`` array."""

    __slots__ = ("array",)

    def __init__(self, array: np.ndarray) -> None:
        self.array = array

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PointList) and np.array_equal(self.array, other.array)

    def __hash__(self) -> int:
        return hash(self.array.tobytes())

    def __array__(self, dtype: Any = None, copy: Any = None) -> np.ndarray:
        return self.array if dtype is None else self.array.astype(dtype)

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        return " ".join(f"{format_number(x, precision)},{format_number(y, precision)}" for x, y in self.array.tolist())

    def __repr__(self) -> str:
        return f"PointList({self.array.tolist()!r})"


def as_points(value: PointsLike | str) -> np.ndarray:
    """*value* as a read-only ``(N, 2)`` float array."""
    array = np.array(parse_points(value) if isinstance(value, str) else value, dtype=float)
    if array.size == 0:
        return _EMPTY
    if array.ndim != 2 or array.shape[1] != 2:
        raise ValueError(f"points must have shape (N, 2), got {array.shape}")
    array.flags.writeable = False
    return array

__all__ = ["PointList", "PointsLike", "Polygon", "Polyline", "as_points"]

FULL_CIRCLE: Final = 360.0


class Polyline(Shape, tag="polyline"):
    """``<polyline>``: an open sequence of straight segments."""

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"points"})

    def __init__(self, points: PointsLike | str = (), **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.points = points  # type: ignore[assignment]

    @property
    def points(self) -> np.ndarray:
        """Vertices as a read-only ``(N, 2)`` float array; assign any ``(N, 2)`` array-like or SVG text."""
        raw = self.attributes.get("points")
        if raw is None:
            return _EMPTY
        if not isinstance(raw, PointList):
            raw = PointList(as_points(raw))
            self.attributes["points"] = raw
        return raw.array

    @points.setter
    def points(self, value: PointsLike | str) -> None:
        self.attributes["points"] = PointList(as_points(value))

    @classmethod
    def regular(cls, cx: float, cy: float, radius: float, sides: int, **kwargs: Any) -> Self:
        """Vertices of a regular polygon, starting at the top."""
        step = FULL_CIRCLE / sides
        angles = np.radians(np.arange(sides) * step)
        return cls(np.column_stack((cx + radius * np.sin(angles), cy - radius * np.cos(angles))), **kwargs)

    @property
    def bbox(self) -> BBox:
        pts = self.points
        if not len(pts):
            return BBox(0.0, 0.0, 0.0, 0.0)
        low, high = pts.min(axis=0), pts.max(axis=0)
        return BBox(float(low[0]), float(low[1]), float(high[0] - low[0]), float(high[1] - low[1]))

    def _builder(self) -> PathBuilder:
        builder = PathBuilder()
        for index, (x, y) in enumerate(self.points.tolist()):
            if index == 0:
                builder.move_to(x, y)
            else:
                builder.line_to(x, y)
        return builder

    def local_outline(self) -> PathData:
        return self._builder().build()


class Polygon(Polyline, tag="polygon"):
    """``<polygon>``: a closed ``Polyline``."""

    @property
    def area(self) -> float:
        """Signed-area magnitude (shoelace formula)."""
        x, y = self.points.T
        return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2.0)

    def local_outline(self) -> PathData:
        builder = self._builder()
        return builder.close().build() if len(builder) else builder.build()
