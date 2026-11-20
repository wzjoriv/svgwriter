"""
``PathOperand``: outlines, path conversion and geometric operators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias, Union

from ..._internal._tree import clip_outline
from ...pathdata.data import PathData
from ...transform.transform import TransformLike, as_transform
from ..core import Element
from ._boolean import BooleanOps
from ._constants import NOT_COPIED
from ._measure import Measurement

if TYPE_CHECKING:
    from ..shapes import Path

__all__ = ["Operand", "PathOperand"]

Operand: TypeAlias = Union["PathOperand", PathData, str]


class PathOperand(BooleanOps, Measurement, Element):
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
    svgwriter.elements._behavior.Convertible : Conversions and clipping.

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
        'M0 0 H4 V3 H0 Z'
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
        'M1 1 L5 1 L5 4 L1 4 Z'
        """
        data = self.local_outline()
        clip = clip_outline(self)
        if clip is not None:
            from ...ops.boolean import BooleanOp, combine

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
        from ..shapes import Path

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

    def expand_pattern(self) -> Element:
        """Replace a pattern fill by copies of its tile, clipped to this outline (plain vector graphics).

        Useful for targets without pattern support (plotters, cutters, some
        editors). The stroke, if any, is kept on top.

        Returns
        -------
        Group
            A ``<g>`` with this element's transform holding the clipped tiles
            and an unfilled copy for the stroke.

        Raises
        ------
        ValueError
            If ``fill`` is not a ``<pattern>``.

        See Also
        --------
        svgwriter.Pattern.tiles : The tiles on their own.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dots = svg.Pattern(svg.circle(2, 2, 1), width=4, height=4, pattern_units="userSpaceOnUse")
        >>> expanded = svg.rect(0, 0, 8, 8, fill=dots, stroke="black").expand_pattern()
        >>> [e.tag for e in expanded], len(expanded[0][0])
        (['g', 'rect'], 4)
        """
        from ..paint import Pattern
        from ..shapes import Path
        from ..structure import Group

        pattern = getattr(self.attributes.get("fill"), "element", None)
        if not isinstance(pattern, Pattern):
            raise ValueError(f"<{self.tag}> is not filled with a <pattern>")
        box = self.local_bbox()
        if box is None:
            raise TypeError(f"<{self.tag}> has no known size")
        tiles = Group(pattern.tiles(box, target=box)).clip(Path(self.local_outline()))
        outline = self.clone()
        outline.set("fill", "none")
        outline.discard("transform")
        result = Group(tiles, transform=self.t)
        if outline.get("stroke") not in (None, "none"):
            result.add(outline)
        return result

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
        'M2 0 L3 0 L3 1 L2 1 Z'
        """
        return self._with_data(self.outline().transformed(transform))


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
    >>> from svgwriter.elements._behavior._geometry import union_outline
    >>> union_outline([svg.rect(0, 0, 2, 2)]).bbox.width
    2.0
    """
    from ...ops.boolean import union
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
