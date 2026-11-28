"""
Inkscape's editable stars, polygons and arcs: paths with ``sodipodi:type`` parameters.
"""

from __future__ import annotations

import math
from typing import Any

from ..._internal._numbers import format_number
from ...model.elements.core import Element
from ...model.elements.shapes import Path
from ...model.transform.matrix import Point
from ._constants import (
    ANGLE_PRECISION,
    ARC_ATTRIBUTES,
    ARC_TYPES,
    FALSE,
    SHAPE_TYPE,
    STAR_ATTRIBUTES,
    STAR_FLATSIDED,
    STAR_RANDOMIZED,
    STAR_ROUNDED,
    TRUE,
    UP,
)
from ._geometry import arc_outline, star_outline

__all__ = ["Arc", "Star", "shape"]


def _angle(radians: float) -> str:
    return format_number(radians, ANGLE_PRECISION)


def _number(element: Element, name: str, default: float = 0.0) -> float:
    value = element.attributes.get(name)
    return default if value is None else float(value)


class _Shape:
    shape_type = ""

    def __init__(self, path: Element) -> None:
        if not isinstance(path, Path) or path.attributes.get(SHAPE_TYPE) != self.shape_type:
            raise ValueError(f"<{path.tag}> is not an Inkscape {self.shape_type} "
                             f"(sodipodi:type=\"{self.shape_type}\" on a path)")
        self.path = path

    def _store(self, values: dict[str, Any]) -> None:
        self.path.attributes.update(values)
        self.redraw()

    def redraw(self) -> None:
        """Recompute the path data from the parameters."""
        raise NotImplementedError

    @property
    def center(self) -> Point:
        """Centre in the path's own coordinates; assign a point to move it."""
        return Point(_number(self.path, "sodipodi:cx"), _number(self.path, "sodipodi:cy"))

    @center.setter
    def center(self, value: tuple[float, float]) -> None:
        self._store({"sodipodi:cx": float(value[0]), "sodipodi:cy": float(value[1])})


class Star(_Shape):
    """The editable parameters of an Inkscape star or polygon.

    A live view on a ``<path sodipodi:type="star">``: reading a property reads the
    ``sodipodi:`` attribute, and assigning one writes it and redraws ``d`` the way
    Inkscape does, so the file stays an editable star in Inkscape.

    Parameters
    ----------
    path : Path
        A path carrying ``sodipodi:type="star"``.

    Raises
    ------
    ValueError
        If `path` is not an Inkscape star.

    See Also
    --------
    Arc : The same for ellipses and arcs.
    svgwriter.library.paths.star : ``inkscape=True`` builds one.

    Notes
    -----
    Angles are in degrees, clockwise from the x axis (Inkscape stores radians).
    ``inkscape:randomized`` is kept but not applied to the redrawn outline;
    Inkscape applies it again when it opens the file.

    Examples
    --------
    >>> import svgwriter as svg
    >>> star = svg.inkscape.Star.create(50, 50, 40, 20, 5)
    >>> view = svg.inkscape.Star(star)
    >>> view.sides = 6
    >>> star.get("sodipodi:sides"), len(star.d)
    (6, 13)
    """

    shape_type = "star"

    @classmethod
    def create(cls, cx: float, cy: float, outer: float, inner: float, sides: int, *, angle: float = UP,
               flatsided: bool = False, rounded: float = 0.0, **kwargs: Any) -> Path:
        """Build a new star path with Inkscape's parameters.

        Parameters
        ----------
        cx, cy : float
            Centre.
        outer, inner : float
            Radii of the tips and of the notches.
        sides : int
            Number of tips (corners for a polygon).
        angle : float, optional
            Direction of the first tip in degrees. Defaults to -90 (up).
        flatsided : bool, optional
            A regular polygon instead of a star. Defaults to False.
        rounded : float, optional
            Inkscape's rounding factor; 0 keeps sharp corners. Defaults to 0.
        **kwargs
            Presentation attributes for the path.

        Returns
        -------
        Path
            The star, with ``sodipodi:`` parameters and matching ``d``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.inkscape.Star.create(0, 0, 10, 5, 4).get("sodipodi:type")
        'star'
        """
        first = math.radians(angle)
        path = Path(**kwargs)
        path.attributes.update({
            SHAPE_TYPE: cls.shape_type, "sodipodi:sides": sides, "sodipodi:cx": float(cx), "sodipodi:cy": float(cy),
            "sodipodi:r1": float(outer), "sodipodi:r2": float(inner), "sodipodi:arg1": _angle(first),
            "sodipodi:arg2": _angle(first + math.pi / sides), STAR_FLATSIDED: TRUE if flatsided else FALSE,
            STAR_ROUNDED: float(rounded), STAR_RANDOMIZED: 0,
        })
        cls(path).redraw()
        return path

    def redraw(self) -> None:
        """Recompute ``d`` from the parameters, as Inkscape does.

        Examples
        --------
        >>> import svgwriter as svg
        >>> star = svg.inkscape.Star.create(0, 0, 10, 5, 3)
        >>> star.d = "M0 0"
        >>> svg.inkscape.Star(star).redraw()
        >>> len(star.d)
        7
        """
        centre = self.center
        outline = star_outline(centre.x, centre.y, (self.outer, self.inner),
                               (_number(self.path, STAR_ATTRIBUTES["arg1"]), _number(self.path, STAR_ATTRIBUTES["arg2"])),
                               self.sides, flatsided=self.flatsided, rounded=self.rounded)
        self.path.d = outline.build()  # type: ignore[attr-defined]

    @property
    def outer(self) -> float:
        """Radius of the tips (``sodipodi:r1``)."""
        return _number(self.path, STAR_ATTRIBUTES["r1"])

    @outer.setter
    def outer(self, value: float) -> None:
        self._store({STAR_ATTRIBUTES["r1"]: float(value)})

    @property
    def inner(self) -> float:
        """Radius of the notches (``sodipodi:r2``)."""
        return _number(self.path, STAR_ATTRIBUTES["r2"])

    @inner.setter
    def inner(self, value: float) -> None:
        self._store({STAR_ATTRIBUTES["r2"]: float(value)})

    @property
    def sides(self) -> int:
        """Number of tips or corners (``sodipodi:sides``); the notch angle follows."""
        return int(_number(self.path, STAR_ATTRIBUTES["sides"]))

    @sides.setter
    def sides(self, value: int) -> None:
        twist = self._twist()
        self.path.attributes[STAR_ATTRIBUTES["sides"]] = int(value)
        self._store({STAR_ATTRIBUTES["arg2"]: _angle(_number(self.path, STAR_ATTRIBUTES["arg1"]) + math.pi / value + twist)})

    @property
    def angle(self) -> float:
        """Direction of the first tip in degrees (``sodipodi:arg1``); the notches turn with it."""
        return math.degrees(_number(self.path, STAR_ATTRIBUTES["arg1"]))

    @angle.setter
    def angle(self, value: float) -> None:
        turn = math.radians(value) - _number(self.path, STAR_ATTRIBUTES["arg1"])
        self._store({STAR_ATTRIBUTES["arg1"]: _angle(math.radians(value)),
                     STAR_ATTRIBUTES["arg2"]: _angle(_number(self.path, STAR_ATTRIBUTES["arg2"]) + turn)})

    def _twist(self) -> float:
        arg1, arg2 = _number(self.path, STAR_ATTRIBUTES["arg1"]), _number(self.path, STAR_ATTRIBUTES["arg2"])
        return arg2 - arg1 - math.pi / max(self.sides, 1)

    @property
    def skew(self) -> float:
        """How far the notches turn away from halfway between tips, in degrees."""
        return math.degrees(self._twist())

    @skew.setter
    def skew(self, value: float) -> None:
        arg1 = _number(self.path, STAR_ATTRIBUTES["arg1"])
        self._store({STAR_ATTRIBUTES["arg2"]: _angle(arg1 + math.pi / self.sides + math.radians(value))})

    @property
    def flatsided(self) -> bool:
        """A regular polygon (``inkscape:flatsided``) instead of a star."""
        return str(self.path.attributes.get(STAR_FLATSIDED, FALSE)).lower() == TRUE

    @flatsided.setter
    def flatsided(self, value: bool) -> None:
        self._store({STAR_FLATSIDED: TRUE if value else FALSE})

    @property
    def rounded(self) -> float:
        """Inkscape's rounding factor (``inkscape:rounded``); 0 is sharp."""
        return _number(self.path, STAR_ROUNDED)

    @rounded.setter
    def rounded(self, value: float) -> None:
        self._store({STAR_ROUNDED: float(value)})


class Arc(_Shape):
    """The editable parameters of an Inkscape ellipse, arc or pie slice.

    A live view on a ``<path sodipodi:type="arc">``; assigning a property writes the
    ``sodipodi:`` attribute and redraws ``d``.

    Parameters
    ----------
    path : Path
        A path carrying ``sodipodi:type="arc"``.

    Raises
    ------
    ValueError
        If `path` is not an Inkscape arc.

    See Also
    --------
    Star : The same for stars and polygons.

    Notes
    -----
    Angles are in degrees, clockwise from the x axis (Inkscape stores radians).

    Examples
    --------
    >>> import svgwriter as svg
    >>> pie = svg.inkscape.Arc.create(0, 0, 10, 10, start=0, end=90)
    >>> svg.inkscape.Arc(pie).kind
    'slice'
    """

    shape_type = "arc"

    @classmethod
    def create(cls, cx: float, cy: float, rx: float, ry: float, *, start: float = 0.0, end: float = 0.0,
               kind: str = ARC_TYPES[0], **kwargs: Any) -> Path:
        """Build a new arc path with Inkscape's parameters.

        Parameters
        ----------
        cx, cy : float
            Centre.
        rx, ry : float
            Radii.
        start, end : float, optional
            Angles in degrees; equal angles give a whole ellipse. Default to 0.
        kind : {"slice", "arc", "chord"}, optional
            A pie slice, an open arc or a closed chord. Defaults to ``"slice"``.
        **kwargs
            Presentation attributes for the path.

        Returns
        -------
        Path
            The arc, with ``sodipodi:`` parameters and matching ``d``.

        Raises
        ------
        ValueError
            If `kind` is unknown.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.inkscape.Arc.create(5, 5, 4, 2).bbox
        BBox(x=1.0, y=3.0, width=8.0, height=4.0)
        """
        path = Path(**kwargs)
        path.attributes.update({
            SHAPE_TYPE: cls.shape_type, ARC_ATTRIBUTES["cx"]: float(cx), ARC_ATTRIBUTES["cy"]: float(cy),
            ARC_ATTRIBUTES["rx"]: float(rx), ARC_ATTRIBUTES["ry"]: float(ry),
        })
        view = cls(path)
        if start != end:
            path.attributes.update({ARC_ATTRIBUTES["start"]: _angle(math.radians(start)),
                                    ARC_ATTRIBUTES["end"]: _angle(math.radians(end))})
        view.kind = kind
        return path

    def redraw(self) -> None:
        """Recompute ``d`` from the parameters, as Inkscape does."""
        centre = self.center
        outline = arc_outline(centre.x, centre.y, self.rx, self.ry, _number(self.path, ARC_ATTRIBUTES["start"]),
                              _number(self.path, ARC_ATTRIBUTES["end"], math.tau), self.kind)
        if outline is not None:
            self.path.d = outline.build()  # type: ignore[attr-defined]

    @property
    def rx(self) -> float:
        """Horizontal radius (``sodipodi:rx``)."""
        return _number(self.path, ARC_ATTRIBUTES["rx"])

    @rx.setter
    def rx(self, value: float) -> None:
        self._store({ARC_ATTRIBUTES["rx"]: float(value)})

    @property
    def ry(self) -> float:
        """Vertical radius (``sodipodi:ry``)."""
        return _number(self.path, ARC_ATTRIBUTES["ry"])

    @ry.setter
    def ry(self, value: float) -> None:
        self._store({ARC_ATTRIBUTES["ry"]: float(value)})

    @property
    def start(self) -> float:
        """Start angle in degrees (``sodipodi:start``)."""
        return math.degrees(_number(self.path, ARC_ATTRIBUTES["start"]))

    @start.setter
    def start(self, value: float) -> None:
        self._store({ARC_ATTRIBUTES["start"]: _angle(math.radians(value))})

    @property
    def end(self) -> float:
        """End angle in degrees (``sodipodi:end``); a whole turn when unset."""
        return math.degrees(_number(self.path, ARC_ATTRIBUTES["end"], math.tau))

    @end.setter
    def end(self, value: float) -> None:
        self._store({ARC_ATTRIBUTES["end"]: _angle(math.radians(value))})

    @property
    def kind(self) -> str:
        """``"slice"``, ``"arc"`` (open) or ``"chord"`` (``sodipodi:arc-type``)."""
        value = self.path.attributes.get(ARC_ATTRIBUTES["kind"])
        if value is None:
            return ARC_TYPES[1] if str(self.path.attributes.get("sodipodi:open", "")).lower() == TRUE else ARC_TYPES[0]
        return str(value)

    @kind.setter
    def kind(self, value: str) -> None:
        if value not in ARC_TYPES:
            raise ValueError(f"unknown arc type {value!r}; choose one of {', '.join(ARC_TYPES)}")
        self.path.attributes.pop("sodipodi:open", None)
        self._store({ARC_ATTRIBUTES["kind"]: value})


def shape(element: Element) -> Star | Arc | None:
    """The editable Inkscape star or arc behind *element*, or None for any other element.

    Parameters
    ----------
    element : Element
        Any element, typically one read from an Inkscape file.

    Returns
    -------
    Star, Arc or None
        A live view of the parameters.

    Examples
    --------
    >>> import svgwriter as svg
    >>> type(svg.inkscape.shape(svg.inkscape.Star.create(0, 0, 4, 2, 5))).__name__
    'Star'
    >>> svg.inkscape.shape(svg.rect(0, 0, 1, 1)) is None
    True
    """
    kinds = {Star.shape_type: Star, Arc.shape_type: Arc}
    found = kinds.get(str(element.attributes.get(SHAPE_TYPE)))
    return found(element) if found is not None and isinstance(element, Path) else None


