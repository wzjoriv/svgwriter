"""``PathOperand``: outlines, path conversion and geometric operators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Final, TypeAlias, Union

from ..pathdata.data import BBox, PathData
from ..transform.matrix import Matrix, Point
from ..transform.transform import TransformLike, as_transform
from .base import Element

if TYPE_CHECKING:
    from ..ops.boolean import BooleanOp
    from ..ops.measure import Cap, Join
    from .shapes import Path

__all__ = ["Operand", "PathOperand"]

Operand: TypeAlias = Union["PathOperand", PathData, str]
NOT_COPIED: Final = frozenset({"id", "transform", "clip-path"})


class PathOperand(Element):
    """An element with an outline.

    Adds :meth:`to_path`, boolean operators and exact measurement:

    - ``a | b``: union
    - ``a & b``: intersection
    - ``a - b``: difference
    - ``a ^ b``: exclusive or

    Every operator returns a new :class:`~svgwriter.Path` carrying the
    left operand's presentation attributes.

    See Also
    --------
    svgwriter.elements._convert.Convertible : Conversions and clipping.

    Examples
    --------
    >>> import svgwriter as svg
    >>> a, b = svg.rect(0, 0, 10, 10), svg.rect(5, 0, 10, 10)
    >>> (a | b).exact_bbox().width, (a & b).exact_bbox().width
    (15.0, 5.0)
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset()
    """Attributes describing the geometry; not copied by :meth:`to_path`."""

    def local_outline(self) -> PathData:
        """Outline in the element's own coordinates (``t`` and clipping ignored).

        Returns
        -------
        PathData
            The outline; subclasses override this.

        Raises
        ------
        TypeError
            If the element has no outline.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.rect(0, 0, 4, 3).local_outline())
        'M0 0 H4 V3 H0 V0 Z'
        """
        raise TypeError(f"<{self.tag}> has no outline")

    def outline(self) -> PathData:
        """Outline in parent coordinates: clipped by ``clip-path``, then ``t`` applied.

        Returns
        -------
        PathData
            The outline.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.rect(0, 0, 4, 3).translate(1, 1).outline())
        'M1 1 L5 1 L5 4 L1 4 L1 1 Z'
        """
        data = self.local_outline()
        clip = clip_outline(self)
        if clip is not None:
            from ..ops.boolean import BooleanOp, combine

            data = combine(data, clip, BooleanOp.INTERSECTION)
        raw = self.attributes.get(self.transform_attribute)  # type: ignore[attr-defined]
        return data if raw is None else data.transformed(as_transform(raw))

    def to_path(self, **kwargs: Any) -> Path:
        """An equivalent ``<path>`` with ``t`` and any clip baked in.

        Presentation attributes are copied; keywords override them.

        Parameters
        ----------
        **kwargs
            Attributes set on the new path, overriding copied ones.

        Returns
        -------
        Path
            A new ``<path>`` element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 4, 3, fill="red").to_path().get("fill")
        'red'
        """
        from .shapes import Path

        path = Path(self.outline())
        path.attributes.update(
            (k, v) for k, v in self.attributes.items() if k not in NOT_COPIED and k not in self.geometry_attributes
        )
        path.update(**kwargs)
        return path

    def flatten_clip(self) -> Path:
        """The visible area as one ``<path>``: :meth:`to_path` with the clip applied.

        Returns
        -------
        Path
            A new ``<path>`` without clipping.

        Examples
        --------
        >>> import svgwriter as svg
        >>> art = svg.rect(0, 0, 10, 10).clip(svg.rect(0, 0, 5, 5))
        >>> art.flatten_clip().exact_bbox().width
        5.0
        """
        return self.to_path()

    def _with_data(self, data: PathData) -> Path:
        path = self.to_path()
        path.d = data
        return path

    def _result(self, data: PathData) -> Path:
        path = self._with_data(data)
        path.discard("fill-rule")
        return path

    def transformed(self, transform: TransformLike) -> Path:
        """A ``<path>`` with ``t`` and then *transform* baked into its coordinates.

        Parameters
        ----------
        transform : Transform, Matrix or str
            The transform applied after ``t``.

        Returns
        -------
        Path
            A new ``<path>`` with no transform attribute.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.rect(0, 0, 1, 1).transformed("translate(2 0)").d)
        'M2 0 L3 0 L3 1 L2 1 L2 0 Z'
        """
        return self._with_data(self.outline().transformed(transform))

    def _boolean(self, first: Operand, second: Operand, op: BooleanOp) -> Path:
        from ..ops.boolean import combine

        return self._result(combine(first, second, op))  # type: ignore[arg-type]

    def union(self, *others: Operand) -> Path:
        """Area covered by this outline or any of *others*.

        Parameters
        ----------
        *others : PathOperand, PathData or str
            Further outlines to add.

        Returns
        -------
        Path
            A new ``<path>``.

        See Also
        --------
        intersection : Area covered by both.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 2, 2).union(svg.rect(2, 0, 2, 2)).exact_bbox().width
        4.0
        """
        from ..ops.boolean import union

        return self._result(union(self, *others))  # type: ignore[arg-type]

    def intersection(self, other: Operand) -> Path:
        """Area covered by both this outline and *other*.

        Parameters
        ----------
        other : PathOperand, PathData or str
            The outline to intersect with.

        Returns
        -------
        Path
            A new ``<path>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 4, 4).intersection(svg.rect(2, 2, 4, 4)).exact_bbox().width
        2.0
        """
        from ..ops.boolean import BooleanOp

        return self._boolean(self, other, BooleanOp.INTERSECTION)

    def difference(self, other: Operand) -> Path:
        """Area covered by this outline but not by *other*.

        Parameters
        ----------
        other : PathOperand, PathData or str
            The outline to subtract.

        Returns
        -------
        Path
            A new ``<path>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 4, 4).difference(svg.rect(2, 0, 4, 4)).exact_bbox().width
        2.0
        """
        from ..ops.boolean import BooleanOp

        return self._boolean(self, other, BooleanOp.DIFFERENCE)

    def xor(self, other: Operand) -> Path:
        """Area covered by exactly one of this outline and *other*.

        Parameters
        ----------
        other : PathOperand, PathData or str
            The outline to combine with.

        Returns
        -------
        Path
            A new ``<path>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 4, 4).xor(svg.rect(2, 0, 4, 4)).exact_bbox().width
        6.0
        """
        from ..ops.boolean import BooleanOp

        return self._boolean(self, other, BooleanOp.XOR)

    def __or__(self, other: Operand) -> Path:
        return self.union(other) if _operand(other) else NotImplemented

    def __ror__(self, other: Operand) -> Path:
        return self.union(other) if _operand(other) else NotImplemented

    def __and__(self, other: Operand) -> Path:
        return self.intersection(other) if _operand(other) else NotImplemented

    def __rand__(self, other: Operand) -> Path:
        return self.intersection(other) if _operand(other) else NotImplemented

    def __sub__(self, other: Operand) -> Path:
        """``a - b`` is the boolean difference; ``a - (dx, dy)`` translates a copy."""
        if not _operand(other):
            return super().__sub__(other)  # type: ignore[misc]
        return self.difference(other)

    def __rsub__(self, other: Operand) -> Path:
        from ..ops.boolean import BooleanOp

        return self._boolean(other, self, BooleanOp.DIFFERENCE) if _operand(other) else NotImplemented

    def __xor__(self, other: Operand) -> Path:
        return self.xor(other) if _operand(other) else NotImplemented

    def __rxor__(self, other: Operand) -> Path:
        return self.xor(other) if _operand(other) else NotImplemented

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
        from ..ops.measure import DEFAULT_MITER_LIMIT, stroke_to_path

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

    def contains_point(self, x: float, y: float) -> bool:
        """Whether ``(x, y)`` lies inside the filled outline (skia).

        Parameters
        ----------
        x, y : float
            The point, in parent coordinates.

        Returns
        -------
        bool
            True if the point is inside.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 10, 10)
        >>> r.contains_point(5, 5), r.contains_point(20, 5)
        (True, False)
        """
        from ..ops.measure import contains

        return contains(self, x, y)

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


def union_outline(children: Any) -> PathData:
    """Union of the outlines of drawable *children*; raises for children without one.

    Parameters
    ----------
    children : iterable of Element
        The elements to combine; ``<defs>`` and non-drawable children are skipped.

    Returns
    -------
    PathData
        The combined outline, empty if nothing is drawable.

    Raises
    ------
    TypeError
        If a drawable child has no vector outline.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.elements._geometry import union_outline
    >>> union_outline([svg.rect(0, 0, 2, 2)]).bbox.width
    2.0
    """
    from ..ops.boolean import union
    from ._transformable import Transformable

    parts = []
    for child in children:
        if child.tag == "defs" or not isinstance(child, Transformable):
            continue
        if not isinstance(child, PathOperand):
            raise TypeError(f"<{child.tag}> has no vector outline, so its group cannot become a path")
        parts.append(child)
    if not parts:
        return PathData()
    return parts[0].outline() if len(parts) == 1 else union(*parts)


def resolve(element: Element, value: Any) -> Element | None:
    """The element an attribute value refers to, if it can be found.

    Parameters
    ----------
    element : Element
        The element holding the value; its root is searched for ids.
    value : object
        A reference, ``#id``, ``url(#id)`` text, or None.

    Returns
    -------
    Element or None
        The referenced element, or None.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.elements._geometry import resolve
    >>> g = svg.group(svg.circle(0, 0, 1, id="dot"))
    >>> resolve(g, "url(#dot)").tag
    'circle'
    """
    target = getattr(value, "element", None)
    if isinstance(target, Element):
        return target
    if value is None:
        return None
    text = str(value.svg_value() if hasattr(value, "svg_value") else value).strip()
    if text.startswith("url(") and text.endswith(")"):
        text = text[4:-1].strip("'\" ")
    return element.root().get_element_by_id(text[1:]) if text.startswith("#") else None


def clip_outline(element: Element) -> PathData | None:
    """The clip region of *element* in its local coordinates, or ``None``.

    Parameters
    ----------
    element : Element
        The clipped element.

    Returns
    -------
    PathData or None
        The clip outline, or None when the element is not clipped.

    Raises
    ------
    TypeError
        If ``clip-path`` refers to something other than a ``<clipPath>``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.elements._geometry import clip_outline
    >>> clip_outline(svg.rect(0, 0, 9, 9)) is None
    True
    """
    clip = resolve(element, element.attributes.get("clip-path"))
    if clip is None:
        return None
    if not isinstance(clip, PathOperand):
        raise TypeError(f"clip-path refers to <{clip.tag}>, not a <clipPath>")
    data = clip.outline()
    if str(clip.get("clipPathUnits", "userSpaceOnUse")) == "objectBoundingBox":
        box = element.local_outline().bbox if isinstance(element, PathOperand) else None
        if box is None:
            return PathData()
        data = data.transformed(Matrix(box.width, 0, 0, box.height, box.x, box.y))
    return data


def _operand(value: object) -> bool:
    return isinstance(value, (PathOperand, PathData, str))
