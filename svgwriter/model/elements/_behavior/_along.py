"""
Positions along an outline by fraction of its length, sub-paths, and corner rounding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ...._internal._page import to_page
from ...transform.matrix import Point

if TYPE_CHECKING:
    from ....ops.corners import Corner, CornerFilter, Fillet
    from ...attributes.length import Length
    from ..shapes import Path

__all__ = ["AlongPath"]


class AlongPath:
    """Walking an outline; mixed into :class:`~svgwriter.model.elements.PathOperand`.

    Positions are fractions of the total length (0 is the start, 1 the end),
    measured on the outline in parent coordinates.
    """

    __slots__ = ()

    def at(self, t: float) -> Point:
        """The point a fraction *t* of the way along the outline.

        Parameters
        ----------
        t : float
            Fraction of the total length, clamped to 0..1.

        Returns
        -------
        Point
            The position.

        Raises
        ------
        ValueError
            If the outline has zero length.

        See Also
        --------
        tangent_at : The direction there.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.line(0, 0, 10, 0).at(0.25)
        Point(x=2.5, y=0.0)
        """
        from ....ops.measure import point_at_length

        return point_at_length(self, t * self.total_length())  # type: ignore[arg-type, attr-defined]

    def tangent_at(self, t: float) -> Point:
        """The unit direction of travel a fraction *t* of the way along the outline.

        Parameters
        ----------
        t : float
            Fraction of the total length, clamped to 0..1.

        Returns
        -------
        Point
            A unit vector.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.line(0, 0, 0, 10).tangent_at(0.5)
        Point(x=0.0, y=1.0)
        """
        from ....ops.measure import tangent_at_length

        return tangent_at_length(self, t * self.total_length())  # type: ignore[arg-type, attr-defined]

    def normal_at(self, t: float) -> Point:
        """The unit normal a fraction *t* of the way along: the tangent turned 90 degrees counter-clockwise on screen.

        For outlines drawn clockwise on screen, as rectangles, circles and
        ellipses are, it points outwards.

        Parameters
        ----------
        t : float
            Fraction of the total length, clamped to 0..1.

        Returns
        -------
        Point
            A unit vector.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 10, 10).normal_at(0.125)
        Point(x=0.0, y=-1.0)
        """
        tangent = self.tangent_at(t)
        return Point(tangent.y, -tangent.x)

    def sample(self, count: int) -> list[Point]:
        """*count* points evenly spaced along the outline.

        A closed outline is split into *count* equal steps without repeating
        the start; an open one includes both ends.

        Parameters
        ----------
        count : int
            How many points; at least 1.

        Returns
        -------
        list of Point
            The points in drawing order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.line(0, 0, 10, 0).sample(3)
        [Point(x=0.0, y=0.0), Point(x=5.0, y=0.0), Point(x=10.0, y=0.0)]
        """
        from ....ops.along import sample

        return sample(self, count)  # type: ignore[arg-type]

    def between(self, start: Length | float = 0.0, end: Length | float | None = None, *,
                by: Literal["fraction", "length"] = "fraction") -> Path:
        """The part of the outline from *start* to *end*, as a new ``<path>``.

        Parameters
        ----------
        start, end : float or Length, optional
            Where the piece begins and ends: fractions of the total length, or
            distances from the start with ``by="length"``. Default to the
            start and the end of the outline.
        by : {"fraction", "length"}, optional
            How *start* and *end* are measured. Defaults to "fraction".

        Returns
        -------
        Path
            The piece, with this element's presentation attributes.

        Raises
        ------
        ValueError
            If *end* comes before *start*, or *by* is unknown.

        Examples
        --------
        >>> import svgwriter as svg
        >>> line = svg.line(0, 0, 10, 0, stroke="red")
        >>> str(line.between(0.2, 0.5).d), str(line.between(1, 4, by="length").d)
        ('M2 0 L5 0', 'M1 0 L4 0')
        """
        from ....ops.measure import segment

        if by not in ("fraction", "length"):
            raise ValueError(f"by must be 'fraction' or 'length', got {by!r}")
        total = self.total_length()  # type: ignore[attr-defined]
        low = to_page(start, self) * (total if by == "fraction" else 1.0)
        high = total if end is None else to_page(end, self) * (total if by == "fraction" else 1.0)
        return self._result(segment(self, low, high))  # type: ignore[arg-type, attr-defined, no-any-return]

    def corners(self) -> list[Corner]:
        """The sharp vertices of the outline.

        Returns
        -------
        list of Corner
            Each corner's vertex number, position and turning angle.

        See Also
        --------
        round_corners : Replace them with fillets.

        Examples
        --------
        >>> import svgwriter as svg
        >>> [(c.index, c.angle.degrees) for c in svg.polyline([(0, 0), (10, 0), (10, 10)]).corners()]
        [(1, 90.0)]
        """
        from ....ops.corners import corners

        return corners(self)  # type: ignore[arg-type]

    def round_corners(self, radius: Length | float, where: CornerFilter = None, *, fillet: Fillet = "arc") -> Path:
        """A ``<path>`` with sharp corners replaced by fillets of *radius*.

        Parameters
        ----------
        radius : float or Length
            Fillet radius; fillets shrink where the sides are too short.
        where : callable, iterable of int or None, optional
            Which corners: all (None), those a predicate on `Corner` accepts,
            or vertex numbers from :meth:`corners`. Defaults to None.
        fillet : {"arc", "quad"}, optional
            A circular arc, or a quadratic curve pulled towards the old vertex. Defaults to "arc".

        Returns
        -------
        Path
            The rounded outline, with this element's presentation attributes.

        Raises
        ------
        ValueError
            If a listed vertex is not a corner.

        Examples
        --------
        >>> import svgwriter as svg
        >>> tri = svg.polygon([(0, 0), (10, 0), (0, 10)])
        >>> len(tri.round_corners(1).corners()), len(tri.round_corners(1, where=lambda c: c.angle > 100).corners())
        (0, 1)
        """
        from ....ops.corners import round_corners

        return self._result(round_corners(self, to_page(radius, self), where, fillet=fillet))  # type: ignore[arg-type, attr-defined, no-any-return]

    def round_corner(self, index: int, radius: Length | float, *, fillet: Fillet = "arc") -> Path:
        """A ``<path>`` with the corner at vertex *index* rounded.

        Parameters
        ----------
        index : int
            The vertex number, as :meth:`corners` reports it.
        radius : float or Length
            Fillet radius.
        fillet : {"arc", "quad"}, optional
            A circular arc or a quadratic curve. Defaults to "arc".

        Returns
        -------
        Path
            The outline with that one corner rounded.

        Raises
        ------
        ValueError
            If the vertex is not a corner.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.polyline([(0, 0), (10, 0), (10, 10)]).round_corner(1, 2).d)
        'M0 0 L8 0 A2 2 0 0 1 10 2 L10 10'
        """
        return self.round_corners(radius, [index], fillet=fillet)
