"""
The shortest ``transform`` text for a matrix.
"""

from __future__ import annotations

from typing import Any

from ..._internal._constants import DEFAULT_PRECISION
from ..._internal._numbers import format_number

__all__ = ["MatrixText"]


def _inside(box: Any, x: float, y: float) -> bool:
    """Whether ``(x, y)`` lies within the box (edges included)."""
    return box.x <= x <= box.x + box.width and box.y <= y <= box.y + box.height


class MatrixText:
    """Serialization of :class:`~svgwriter.model.transform.Matrix` as ``transform`` text."""

    __slots__ = ()

    def svg_value(self, precision: int = DEFAULT_PRECISION, *, anchor: tuple[float, float] | None = None,
                  box: Any = None) -> str:
        """The shortest ``transform`` text for this matrix.

        Rigid motions become ``rotate(a cx cy)``; otherwise the parts of
        ``translate rotate skewX scale`` that are not identity, falling back
        to ``matrix(...)`` when that is shorter.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places. Defaults to the library default precision.
        anchor : (float, float), optional
            The element's anchor. When a pure rotation's
            centre would fall outside *box*, the text becomes
            ``translate(dx dy) rotate(a px py)`` about this point instead,
            which is what a person would write. Defaults to None.
        box : BBox, optional
            The element's local bounding box, used with *anchor*. Defaults to None.

        Returns
        -------
        str
            Text suitable for a ``transform`` attribute; empty for the identity.

        Examples
        --------
        >>> from svgwriter.model.transform import Matrix
        >>> Matrix.rotate(90, 5, 5).svg_value()
        'rotate(90 5 5)'
        >>> (Matrix.translate(10, 5) @ Matrix.scale(2, 3)).svg_value()
        'matrix(2 0 0 3 10 5)'
        >>> Matrix.skew_x(30).svg_value()
        'skewX(30)'
        """
        from .matrix import Matrix

        def num(value: float) -> str:
            return format_number(value, precision)

        def zero(value: float) -> bool:
            return num(value) in ("0", "-0")

        tx, ty, angle, skew, sx, sy = self.decompose()
        if zero(sx - 1) and zero(sy - 1) and zero(skew) and not zero(angle):
            rotation = Matrix.rotate(angle)
            denominator = (1 - rotation.a) ** 2 + rotation.b ** 2
            cx = ((1 - rotation.a) * tx - rotation.b * ty) / denominator
            cy = (rotation.b * tx + (1 - rotation.a) * ty) / denominator
            if anchor is not None and box is not None and not _inside(box, cx, cy):
                px, py = float(anchor[0]), float(anchor[1])
                moved = self.apply(px, py)
                dx, dy = moved.x - px, moved.y - py
                shift = "" if zero(dx) and zero(dy) else (
                    f"translate({num(dx)}) " if zero(dy) else f"translate({num(dx)} {num(dy)}) ")
                return f"{shift}rotate({num(angle)} {num(px)} {num(py)})"
            centre = "" if zero(cx) and zero(cy) else f" {num(cx)} {num(cy)}"
            return f"rotate({num(angle)}{centre})"
        parts = []
        if not (zero(tx) and zero(ty)):
            parts.append(f"translate({num(tx)})" if zero(ty) else f"translate({num(tx)} {num(ty)})")
        if not zero(angle):
            parts.append(f"rotate({num(angle)})")
        if not zero(skew):
            parts.append(f"skewX({num(skew)})")
        if not (zero(sx - 1) and zero(sy - 1)):
            parts.append(f"scale({num(sx)})" if zero(sx - sy) else f"scale({num(sx)} {num(sy)})")
        text = " ".join(parts)
        full = "matrix({})".format(" ".join(num(v) for v in self.as_tuple()))
        return text if len(text) <= len(full) else full
