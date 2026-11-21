"""
Whole-figure helpers of the path builder: existing data, circles and polygons.
"""

from __future__ import annotations

import math

from ..._internal._typing import Self
from ._constants import FULL_CIRCLE, QUARTER_TURN
from .data import PathData

__all__ = ["ShapeCommands"]


class ShapeCommands:
    """Appending existing data, circles and regular polygons to :class:`~svgwriter.model.pathdata.PathBuilder`."""

    __slots__ = ()

    def extend(self, data: PathData | str) -> Self:
        """Append existing path data.

        Every command of `data` is pushed in order, so the current point follows it.

        Parameters
        ----------
        data : PathData or str
            Commands to append; text is parsed and must begin with a ``moveto``.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        Raises
        ------
        PathSyntaxError
            If `data` is text that is not valid path data.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> str(PathBuilder().move_to(0, 0).extend("M5 5 l1 1"))
        'M0 0 M5 5 l1 1'
        """
        if isinstance(data, str):
            text = data.strip()
            if text and text[0] not in "Mm":
                text = f"M{self._current.x} {self._current.y} {text}"
                for command in list(PathData(text))[1:]:
                    self._push(command)
                return self
            data = PathData(text)
        for command in data:
            self._push(command)
        return self

    def circle(self, cx: float, cy: float, r: float) -> Self:
        """Append a full circle as two half arcs.

        The subpath starts at the leftmost point and is closed.

        Parameters
        ----------
        cx, cy : float
            Centre of the circle.
        r : float
            Radius.

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        See Also
        --------
        regular_polygon : Append a closed polygon.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> str(PathBuilder().circle(5, 5, 5))
        'M0 5 A5 5 0 0 1 10 5 A5 5 0 0 1 0 5 Z'
        """
        self.move_to(cx - r, cy)
        self.arc_to(r, r, 0, False, True, cx + r, cy)
        self.arc_to(r, r, 0, False, True, cx - r, cy)
        return self.close()

    def regular_polygon(self, cx: float, cy: float, radius: float, sides: int, rotation: float = -QUARTER_TURN) -> Self:
        """Append a closed regular polygon.

        Vertices are spaced evenly on a circle; the first vertex points up by default.

        Parameters
        ----------
        cx, cy : float
            Centre of the polygon.
        radius : float
            Distance from the centre to each vertex.
        sides : int
            Number of sides; at least 3.
        rotation : float, optional
            Angle of the first vertex in degrees, measured clockwise from the
            positive x axis. Defaults to -90 (pointing up).

        Returns
        -------
        PathBuilder
            The builder itself, for chaining.

        Raises
        ------
        ValueError
            If `sides` is less than 3.

        See Also
        --------
        circle : Append a full circle.

        Examples
        --------
        >>> from svgwriter.model.pathdata import PathBuilder
        >>> str(PathBuilder().regular_polygon(0, 0, 10, 3))
        'M0 -10 L8.6603 5 L-8.6603 5 Z'
        """
        if sides < 3:
            raise ValueError("a polygon needs at least three sides")
        for i in range(sides):
            angle = math.radians(rotation + FULL_CIRCLE * i / sides)
            x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
            if i == 0:
                self.move_to(x, y)
            else:
                self.line_to(x, y)
        return self.close()
