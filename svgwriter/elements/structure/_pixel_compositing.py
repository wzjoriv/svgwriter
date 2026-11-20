"""
Compositing for :class:`~svgwriter.elements.structure.Pixels`: operators and drawing elements onto a pixel grid.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ...ops.composite import Operator
    from ._pixels import Pixels

__all__ = ["PixelCompositing"]


class PixelCompositing:
    """Porter-Duff and blend operators between pixel grids, elements and documents."""

    __slots__ = ()

    def composite(self, backdrop: Pixels | np.ndarray, operator: Operator = "over", *, k: Sequence[float] = ()) -> Pixels:
        """Composite these pixels onto *backdrop*, pixel for pixel.

        ``a | b``, ``a & b``, ``a - b`` and ``a ^ b`` are ``over``, ``in``,
        ``out`` and ``xor``; ``a * b`` is the ``multiply`` blend. To combine
        images, composite their pixels: ``image.pixels | other.pixels``.

        Parameters
        ----------
        backdrop : Pixels or numpy.ndarray
            Pixels underneath, or a straight RGBA array; it broadcasts, so
            ``(1, 1, 4)`` is a solid color.
        operator : CompositeOperator, BlendMode or str, optional
            An ``feComposite`` operator or ``feBlend`` mode. Defaults to ``"over"``.
        k : sequence of float, optional
            ``(k1, k2, k3, k4)`` for ``"arithmetic"``. Defaults to ().

        Returns
        -------
        Pixels
            New pixels; both operands are left unchanged.

        Raises
        ------
        ValueError
            If the operator is unknown or the pixel shapes do not broadcast.

        See Also
        --------
        svgwriter.ops.composite_rgba : The same on raw RGBA arrays.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> glass = Pixels.from_array(np.full((2, 2, 3), 1.0), alpha=0.25)
        >>> (glass | np.array([[[0, 0, 0, 1.0]]])).rgba()[0, 0].tolist()
        [0.25, 0.25, 0.25, 1.0]
        """
        from ...ops.composite import composite_rgba

        under = backdrop.rgba() if isinstance(backdrop, PixelCompositing) else np.asarray(backdrop, dtype=np.float32)
        try:
            return type(self).from_array(composite_rgba(self.rgba(), under, operator, k=k))
        except ValueError as error:
            if "broadcast" not in str(error):
                raise
            raise ValueError(f"pixel shapes {self.shape} and {under.shape[:2]} differ; "
                             "rasterize the elements onto one canvas first") from None

    def on_grid(self, element: object) -> Pixels:
        """Render *element* onto a transparent canvas the size of these pixels.

        The element's user units are pixels of this grid, so ``circle(10, 10, 5)``
        lands around pixel ``(10, 10)``. This is how ``pixels | element`` and the
        other operators composite shapes, text and whole documents with an image.

        Parameters
        ----------
        element : Element or Document
            What to draw; it is copied, never moved.

        Returns
        -------
        Pixels
            The rendering, with the same shape as these pixels.

        Raises
        ------
        TypeError
            If *element* is neither an element nor a document.

        See Also
        --------
        composite : Combine two equal-sized grids.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> from svgwriter.elements.structure import Pixels
        >>> grid = Pixels.from_array(np.zeros((8, 8, 3)))
        >>> grid.on_grid(svg.rect(0, 0, 4, 8, fill="red")).rgba()[4, 1].tolist()
        [1.0, 0.0, 0.0, 1.0]
        """
        from ...document import Document
        from ..core import Element

        rows, columns = self.shape
        if isinstance(element, Document):
            source = element.root.clone()
        elif isinstance(element, Element):
            source = element.clone()
        else:
            raise TypeError(f"cannot draw {type(element).__name__} onto pixels; pass an element or a document")
        canvas = Document(columns, rows)
        canvas.add(source)
        return type(self).from_array(canvas.rasterize(size=(columns, rows)))

    def _pair(self, other: object, operator: str) -> Pixels:
        from ...document import Document
        from ..core import Element

        if isinstance(other, (Element, Document)):
            other = self.on_grid(other)
        return self.composite(other, operator) if isinstance(other, (PixelCompositing, np.ndarray)) else NotImplemented  # type: ignore[return-value]

    def __or__(self, other: object) -> Pixels:
        return self._pair(other, "over")

    def __and__(self, other: object) -> Pixels:
        return self._pair(other, "in")

    def __sub__(self, other: object) -> Pixels:
        return self._pair(other, "out")

    def __xor__(self, other: object) -> Pixels:
        return self._pair(other, "xor")

    def __mul__(self, other: object) -> Pixels:
        return self._pair(other, "multiply")
