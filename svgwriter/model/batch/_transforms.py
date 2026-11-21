"""
Per-item transforms of a batch: translation, rotation and scaling with numpy-broadcast arguments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal._typing import Self
from ._columns import frozen
from ._constants import IDENTITY_ROW

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

__all__ = ["ItemTransforms", "compose"]


def compose(outer: np.ndarray, inner: np.ndarray) -> np.ndarray:
    """``outer @ inner`` for ``(N, 6)`` stacks of ``(a, b, c, d, e, f)`` matrices."""
    oa, ob, oc, od, oe, of = outer.T
    ia, ib, ic, id_, ie, if_ = inner.T
    return np.stack([oa * ia + oc * ib, ob * ia + od * ib, oa * ic + oc * id_, ob * ic + od * id_,
                     oa * ie + oc * if_ + oe, ob * ie + od * if_ + of], axis=1)


def _about(linear: np.ndarray, pivots: np.ndarray) -> np.ndarray:
    """``translate(p) @ L @ translate(-p)`` per item, from ``(N, 4)`` linear parts and ``(N, 2)`` pivots."""
    a, b, c, d = linear.T
    px, py = pivots.T
    return np.stack([a, b, c, d, px - a * px - c * py, py - b * px - d * py], axis=1)


class ItemTransforms:
    """Translate, rotate and scale every item of a batch; mixed into :class:`~svgwriter.model.batch.Batch`.

    Arguments are scalars or arrays that broadcast against the items (numpy rules), so one call
    moves every item by its own amount. Each item turns and scales about its own centre unless
    *about* gives pivots. The transform of the batch's ``<g>`` itself is :attr:`t`.
    """

    __slots__ = ()

    def _per_item(self, value: ArrayLike) -> np.ndarray:
        count = len(self)  # type: ignore[arg-type]
        try:
            return np.broadcast_to(np.asarray(value, dtype=float), (count,))
        except ValueError as error:
            raise ValueError(f"expected a scalar or one value per item ({count}), got shape "
                             f"{np.shape(value)}") from error

    def _matrices(self) -> np.ndarray:
        current = self._matrix  # type: ignore[attr-defined]
        return current if current is not None else np.tile(IDENTITY_ROW, (len(self), 1))  # type: ignore[arg-type]

    def _pivots(self, about: tuple[ArrayLike, ArrayLike] | None) -> np.ndarray:
        if about is not None:
            return np.stack([self._per_item(about[0]), self._per_item(about[1])], axis=1)
        anchors = self._anchors()  # type: ignore[attr-defined]
        m = self._matrices()
        return np.stack([m[:, 0] * anchors[:, 0] + m[:, 2] * anchors[:, 1] + m[:, 4],
                         m[:, 1] * anchors[:, 0] + m[:, 3] * anchors[:, 1] + m[:, 5]], axis=1)

    def _apply(self, operation: np.ndarray) -> None:
        self._matrix = frozen(compose(operation, self._matrices()))

    def _each(self, method: str, *columns: np.ndarray, **options: Any) -> Self:
        for index, item in enumerate(self.items):  # type: ignore[attr-defined]
            getattr(item, method)(*(float(column[index]) for column in columns), **options)
        return self

    def translate(self, dx: ArrayLike, dy: ArrayLike = 0.0) -> Self:
        """Move every item by its own ``(dx, dy)`` and return the batch.

        Parameters
        ----------
        dx, dy : float or array_like
            Offsets in user units, broadcast over the items. *dy* defaults to 0.

        Returns
        -------
        Batch
            This batch.

        Raises
        ------
        ValueError
            If an argument does not broadcast to one value per item.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dots = svg.batch.circles([0, 10], 0, 1).translate([5, 0], 2)
        >>> dots.column("transform").tolist()
        [[1.0, 0.0, 0.0, 1.0, 5.0, 2.0], [1.0, 0.0, 0.0, 1.0, 0.0, 2.0]]
        """
        offsets = self._per_item(dx), self._per_item(dy)
        if not self.compact:  # type: ignore[attr-defined]
            return self._each("translate", *offsets)
        operation = np.tile(IDENTITY_ROW, (len(self), 1))  # type: ignore[arg-type]
        operation[:, 4], operation[:, 5] = offsets
        self._apply(operation)
        return self

    def rotate(self, degrees: ArrayLike, *, about: tuple[ArrayLike, ArrayLike] | None = None) -> Self:
        """Turn every item by its own angle (clockwise on screen, in degrees) and return the batch.

        Parameters
        ----------
        degrees : float or array_like
            Angles, broadcast over the items.
        about : (array_like, array_like), optional
            Pivots ``(x, y)`` in the batch's coordinates, broadcast over the items. Defaults to
            each item's centre (its anchor, where it is now).

        Returns
        -------
        Batch
            This batch.

        Examples
        --------
        >>> import svgwriter as svg
        >>> bars = svg.batch.rects([0, 20], 0, 10, 2).rotate([0, 90])
        >>> bars.column("transform").round(3).tolist()[1]
        [0.0, 1.0, -1.0, 0.0, 26.0, -24.0]
        """
        radians = np.radians(self._per_item(degrees))
        return self._linear(np.stack([np.cos(radians), np.sin(radians), -np.sin(radians), np.cos(radians)], axis=1),
                            "rotate", (self._per_item(degrees),), about)

    def scale(self, sx: ArrayLike, sy: ArrayLike | None = None, *,
              about: tuple[ArrayLike, ArrayLike] | None = None) -> Self:
        """Scale every item by its own factors and return the batch.

        Parameters
        ----------
        sx, sy : float or array_like
            Factors along x and y, broadcast over the items; *sy* defaults to *sx*.
        about : (array_like, array_like), optional
            Fixed points, as for :meth:`rotate`. Defaults to each item's centre.

        Returns
        -------
        Batch
            This batch.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dots = svg.batch.circles([0, 10], 0, 1).scale([1, 3])
        >>> dots.bounds().width
        14.0
        """
        x = self._per_item(sx)
        y = x if sy is None else self._per_item(sy)
        zero = np.zeros_like(x)
        return self._linear(np.stack([x, zero, zero, y], axis=1), "scale", (x, y), about)

    def _linear(self, linear: np.ndarray, method: str, arguments: tuple[np.ndarray, ...],
                about: tuple[ArrayLike, ArrayLike] | None) -> Self:
        if not self.compact:  # type: ignore[attr-defined]
            if about is None:
                return self._each(method, *arguments)
            pivots = self._pivots(about)
            for index, item in enumerate(self.items):  # type: ignore[attr-defined]
                getattr(item, method)(*(float(a[index]) for a in arguments), about=tuple(pivots[index]))
            return self
        self._apply(_about(linear, self._pivots(about)))
        return self
