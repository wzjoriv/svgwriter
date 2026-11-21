"""
Placement for transformable elements: anchors, ``place``, ``align`` and ``bounds``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._internal._tree import settle_parent
from ...pathdata.data import BBox
from ...transform.matrix import Point
from ._constants import BASELINE, ORIGIN

if TYPE_CHECKING:
    from ._transformable import E, Pivot, PointLike

__all__ = ["Placement"]


def _target_point(target: Any, name: str) -> Point:
    """The named point of an element's bounds or a box, or a plain point as given."""
    from ._transformable import Transformable

    if isinstance(target, BBox):
        return target.point(name)
    if isinstance(target, Transformable):
        return target._named_point(name)
    try:
        x, y = target
        return Point(float(x), float(y))
    except (TypeError, ValueError):
        raise TypeError(f"align() takes an element, a BBox or an (x, y) point, not {type(target).__name__}") from None


class Placement:
    """Anchors, placing and aligning; mixed into :class:`~svgwriter.elements.Transformable`."""

    __slots__ = ()

    @property
    def anchor(self) -> Point:
        """Pivot in local coordinates; the bounding-box centre unless set.

        Assign a point, or a name read on the element's own box each time,
        so it follows edits: ``"center"``, ``"top"``, ``"bottom"``,
        ``"left"``, ``"right"``, ``"top_left"``, ``"top_right"``,
        ``"bottom_left"``, ``"bottom_right"`` (and the other
        :meth:`BBox.point` names), ``"origin"`` for local ``(0, 0)``, or,
        on text, ``"baseline"`` for the start of its first baseline.
        Assign ``None`` to go back to the centre. The same names work as
        ``about=`` in every transform method and animation preset.

        Raises
        ------
        ValueError
            On assigning an unknown name; the message lists the valid ones.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 10, 4)
        >>> r.anchor
        Point(x=5.0, y=2.0)
        >>> r.anchor = "bottom"
        >>> r.anchor
        Point(x=5.0, y=4.0)
        """
        if isinstance(self._anchor, str):
            return self._local_point(self._anchor)
        if self._anchor is not None:
            return Point(*self._anchor)
        box = self.local_bbox()
        return box.center if box is not None else Point(0.0, 0.0)

    @anchor.setter
    def anchor(self, value: Pivot | None) -> None:
        if isinstance(value, str):
            self._check_point_name(value)
            self._anchor = value
            return
        self._anchor = None if value is None else (float(value[0]), float(value[1]))

    def _point_names(self) -> tuple[str, ...]:
        names = (*BBox.point_names(), ORIGIN)
        return (*names, BASELINE) if type(self)._baseline_point is not Placement._baseline_point else names

    def _check_point_name(self, name: str) -> None:
        if name not in self._point_names():
            raise ValueError(f"unknown pivot {name!r} for <{self.tag}>; choose one of "  # type: ignore[attr-defined]
                             f"{', '.join(self._point_names())}")

    def _baseline_point(self) -> Point | None:
        """Start of the first baseline in local coordinates; None for elements without text."""
        return None

    def _local_point(self, name: str) -> Point:
        """A named pivot in local coordinates, read on the current local box."""
        self._check_point_name(name)
        if name == ORIGIN:
            return Point(0.0, 0.0)
        if name == BASELINE:
            return self._baseline_point()  # type: ignore[return-value]
        box = self.local_bbox()
        if box is None:
            raise TypeError(f"<{self.tag}> has no known size, so it has no {name!r} point")  # type: ignore[attr-defined]
        return box.point(name)

    @property
    def position(self) -> Point:
        """The anchor in parent coordinates; assign to move the element there.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 10, 10)
        >>> r.position = (20, 20)
        >>> r.position
        Point(x=20.0, y=20.0)
        """
        return self.t.apply(*self.anchor)

    @position.setter
    def position(self, value: PointLike) -> None:
        here = self.position
        self.translate(value[0] - here.x, value[1] - here.y)

    def place(self: E, x: float, y: float, *, at: str | None = None) -> E:
        """Move the element so its anchor, or the named point of its bounds, lands on ``(x, y)``.

        Parameters
        ----------
        x, y : float
            Target position in parent coordinates.
        at : str, optional
            A named point of :meth:`bounds` (``"top_left"``, ``"center"``,
            ``"bottom"``, ...; see :meth:`BBox.point`). Defaults to None, which
            uses the anchor.

        Returns
        -------
        Transformable
            This element.

        Raises
        ------
        ValueError
            If `at` is not a known point name.
        TypeError
            If `at` is given and the element's size is unknown.

        See Also
        --------
        align : Place relative to another element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.circle(0, 0, 1).place(10, 20).position
        Point(x=10.0, y=20.0)
        >>> svg.rect(0, 0, 4, 2).place(10, 10, at="bottom_right").bounds()
        BBox(x=6.0, y=8.0, width=4.0, height=2.0)
        """
        if at is None:
            self.position = (x, y)
            return self
        here = self._named_point(at)
        self.translate(x - here.x, y - here.y)
        return self

    def align(self: E, target: Any, at: str = "center", *, to: str | None = None,
              offset: PointLike = (0.0, 0.0)) -> E:
        """Move the element so its point *at* meets the point *to* of *target*.

        Parameters
        ----------
        target : Element, BBox or (float, float)
            What to align with; an element's :meth:`bounds` are used.
        at : str, optional
            Named point of this element's bounds. Defaults to ``"center"``.
        to : str, optional
            Named point of the target. Defaults to `at`, so ``a.align(b, "left")``
            lines up left edges and ``a.align(b, "top", to="bottom")`` stacks
            *a* under *b*.
        offset : (float, float), optional
            Extra shift after aligning, for gaps. Defaults to ``(0, 0)``.

        Returns
        -------
        Transformable
            This element.

        Raises
        ------
        TypeError
            If either size is unknown or `target` is not an element, box or point.

        See Also
        --------
        place : Move to a coordinate.
        BBox.point : The point names.

        Examples
        --------
        >>> import svgwriter as svg
        >>> base = svg.rect(0, 0, 40, 10)
        >>> label = svg.rect(0, 0, 10, 4).align(base, "top", to="bottom", offset=(0, 2))
        >>> label.bounds()
        BBox(x=15.0, y=12.0, width=10.0, height=4.0)
        """
        goal = _target_point(target, to or at)
        return self.place(goal.x + float(offset[0]), goal.y + float(offset[1]), at=at)

    def _named_point(self, name: str) -> Point:
        box = self.bounds()
        if box is None:
            raise TypeError(f"<{self.tag}> has no known size, so it has no {name!r} point")  # type: ignore[attr-defined]
        return box.point(name)

    def bounds(self) -> BBox | None:
        """Bounding box in parent coordinates (after :attr:`t`).

        Returns
        -------
        BBox or None
            The box enclosing the transformed local box, or None when unknown.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 2, 2).translate(5, 5).bounds()
        BBox(x=5.0, y=5.0, width=2.0, height=2.0)
        """
        settle_parent(self)  # type: ignore[arg-type]
        box = self.local_bbox()
        if box is None:
            return None
        m = self.t
        corners = [(box.x, box.y), (box.x + box.width, box.y), (box.x, box.y + box.height),
                   (box.x + box.width, box.y + box.height)]
        return BBox.from_points(m.apply(*p) for p in corners)
