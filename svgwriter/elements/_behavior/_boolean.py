"""
Boolean operations for path operands: union, intersection, difference, xor and their operators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...pathdata.data import PathData

if TYPE_CHECKING:
    from ...ops.boolean import BooleanOp
    from ..shapes import Path
    from ._geometry import Operand

__all__ = ["BooleanOps"]


def _operand(value: object) -> bool:
    from ._geometry import PathOperand

    return isinstance(value, (PathOperand, PathData, str))


class BooleanOps:
    """Boolean methods and operators; mixed into :class:`~svgwriter.elements.PathOperand`."""

    __slots__ = ()

    def _boolean(self, first: Operand, second: Operand, op: BooleanOp) -> Path:
        from ...ops.boolean import combine

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
        from ...ops.boolean import union

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
        from ...ops.boolean import BooleanOp

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
        from ...ops.boolean import BooleanOp

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
        from ...ops.boolean import BooleanOp

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
        from ...ops.boolean import BooleanOp

        return self._boolean(other, self, BooleanOp.DIFFERENCE) if _operand(other) else NotImplemented

    def __xor__(self, other: Operand) -> Path:
        return self.xor(other) if _operand(other) else NotImplemented

    def __rxor__(self, other: Operand) -> Path:
        return self.xor(other) if _operand(other) else NotImplemented

    def _take_place(self, result: Any) -> Any:
        """Put *result* where this element is in its parent, keeping an explicit id."""
        from ._geometry import replace_in_parent

        if result is NotImplemented:
            return result
        replace_in_parent(self, result)
        return result

    def __ior__(self, other: Operand) -> Any:
        """``a |= b``: the union replaces *a* in its parent (a shape becomes a ``<path>``)."""
        return self._take_place(self.__or__(other))

    def __iand__(self, other: Operand) -> Any:
        return self._take_place(self.__and__(other))

    def __isub__(self, other: Operand) -> Any:
        """``a -= b`` cuts *b* out in place; ``a -= (dx, dy)`` moves *a*."""
        if not _operand(other):
            return super().__isub__(other)  # type: ignore[misc]
        return self._take_place(self.__sub__(other))

    def __ixor__(self, other: Operand) -> Any:
        return self._take_place(self.__xor__(other))
