"""
Exact measurement for path operands: simplification, stroking, bounds, hit tests and arc length.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..pathdata.data import BBox
from ..transform.matrix import Point

if TYPE_CHECKING:
    from ..ops.measure import Cap, Join
    from .shapes import Path

__all__ = ["Measurement"]


class Measurement:
    """Measuring an outline; mixed into :class:`~svgwriter.elements._geometry.PathOperand`."""

    __slots__ = ()

    def simplified(self) -> Path:
        """Same area without overlaps or self-intersections (skia).

        Returns
        -------
        Path
            A new ``<path>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 4, 4).simplified().exact_bbox().width
        4.0
        """
        from ..ops.boolean import simplify

        return self._result(simplify(self))

    def stroked(
        self,
        width: float | None = None,
        *,
        cap: Cap | None = None,
        join: Join | None = None,
        miter_limit: float | None = None,
    ) -> Path:
        """The stroke as a filled ``<path>`` (skia).

        Unset arguments come from this element's ``stroke-*`` attributes.
        The result is filled with the stroke paint and has no stroke.

        Parameters
        ----------
        width : float, optional
            Stroke width. Defaults to the element's ``stroke-width``, or 1.
        cap : Cap, optional
            Line cap. Defaults to the element's ``stroke-linecap``, or butt.
        join : Join, optional
            Line join. Defaults to the element's ``stroke-linejoin``, or miter.
        miter_limit : float, optional
            Miter limit. Defaults to the element's ``stroke-miterlimit``.

        Returns
        -------
        Path
            A new filled ``<path>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> outline = svg.line(0, 0, 10, 0, stroke="red").stroked(2)
        >>> outline.exact_bbox().height, outline.get("fill")
        (2.0, 'red')
        """
        from ..attributes.length import Length
        from ..ops._constants import DEFAULT_MITER_LIMIT
        from ..ops.measure import stroke_to_path

        width = width if width is not None else Length.parse(self.get("stroke-width", 1)).to_user_units()
        data = stroke_to_path(
            self,
            width,
            cap=cap or str(self.get("stroke-linecap", "butt")),  # type: ignore[arg-type]
            join=join or str(self.get("stroke-linejoin", "miter")),  # type: ignore[arg-type]
            miter_limit=miter_limit if miter_limit is not None else float(self.get("stroke-miterlimit", DEFAULT_MITER_LIMIT)),
        )
        path = self._result(data)
        path.set("fill", self.get("stroke", "black"))
        for name in ("stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray"):
            path.discard(name)
        return path

    def exact_bbox(self) -> BBox:
        """Tight bounding box of the transformed outline (skia).

        Returns
        -------
        BBox
            The box in parent coordinates.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.circle(5, 5, 5).exact_bbox()
        BBox(x=0.0, y=0.0, width=10.0, height=10.0)
        """
        from ..ops.measure import bounds

        return bounds(self)

    def contains_point(self, x: Any, y: float | None = None) -> Any:
        """Whether points lie inside the filled outline (skia).

        Parameters
        ----------
        x : float, (float, float), Point or array-like
            The x coordinate with `y`, or a point, or an ``(n, 2)`` array of points,
            in parent coordinates.
        y : float, optional
            The y coordinate when `x` is a number. Defaults to None.

        Returns
        -------
        bool or numpy.ndarray
            True when inside; one boolean per point for an array.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 10, 10)
        >>> r.contains_point(5, 5), r.contains_point((20, 5))
        (True, False)
        >>> r.contains_point(np.array([[1, 1], [11, 1], [9, 9]])).tolist()
        [True, False, True]
        """
        import numpy as np

        from ..ops._skia import to_skia

        if y is not None:
            points = np.array([[float(x), float(y)]])
            single = True
        else:
            points = np.asarray(x, dtype=float)
            single = points.ndim == 1
            points = points.reshape(-1, 2)
        outline = to_skia(self.outline(), evenodd=str(self.get("fill-rule", "nonzero")) == "evenodd")
        inside = np.fromiter((outline.contains(px, py) for px, py in points), dtype=bool, count=len(points))
        return bool(inside[0]) if single else inside

    def total_length(self) -> float:
        """Length of the outline, like ``getTotalLength()`` (skia).

        Returns
        -------
        float
            The outline length in user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 10, 5).total_length()
        30.0
        """
        from ..ops.measure import total_length

        return total_length(self)

    def point_at_length(self, distance: float) -> Point:
        """Point *distance* along the outline, like ``getPointAtLength()`` (skia).

        Parameters
        ----------
        distance : float
            Distance from the start of the outline, in user units.

        Returns
        -------
        Point
            The point on the outline.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.line(0, 0, 10, 0).point_at_length(4)
        Point(x=4.0, y=0.0)
        """
        from ..ops.measure import point_at_length

        return point_at_length(self, distance)
