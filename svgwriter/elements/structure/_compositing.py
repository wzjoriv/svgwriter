"""
Porter-Duff operators for images: ``a | b``, ``a & b``, ``a - b``, ``a ^ b`` and ``composite``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Final

from ..base import Element
from ..filters import BlendMode, CompositeOperator

if TYPE_CHECKING:
    from ...ops.composite import Operator
    from ...pathdata.data import BBox
    from ._image import Image

__all__ = ["Compositing"]

GEOMETRY_KEYS: Final = frozenset({"x", "y", "width", "height", "xlink:href", "preserveAspectRatio", "transform", "id"})
SOURCE_AREA: Final = frozenset({CompositeOperator.IN, CompositeOperator.OUT})
BACKDROP_AREA: Final = frozenset({CompositeOperator.ATOP})
DEFAULT_SCALE: Final = 1.0


def _same_raster(a: Element, b: Element) -> bool:
    from ._image import Image

    if not (isinstance(a, Image) and isinstance(b, Image)) or a.pixels is None or b.pixels is None:
        return False
    if not (set(a.attributes) | set(b.attributes)) <= GEOMETRY_KEYS:
        return False
    keys = ("x", "y", "width", "height", "preserveAspectRatio")
    return a.t == b.t and all(a.get(k) == b.get(k) for k in keys) and a.shape == b.shape


def _density(element: Element) -> float | None:
    from ._image import Image

    if not isinstance(element, Image) or element.pixels is None:
        return None
    box = element.bounds()
    if box is None or box.width <= 0 or box.height <= 0:
        return None
    rows, columns = element.shape
    return max(columns / box.width, rows / box.height)


def _canvas(source: Element, backdrop: Element, operator: CompositeOperator | BlendMode) -> BBox:
    boxes = [e.render_bounds() for e in (source, backdrop)]  # type: ignore[attr-defined]
    for element, box in zip((source, backdrop), boxes, strict=True):
        if box is None:
            raise TypeError(f"<{element.tag}> has no known size; give it width and height to composite it")
    if operator in SOURCE_AREA:
        return boxes[0]
    if operator in BACKDROP_AREA:
        return boxes[1]
    return boxes[0].union(boxes[1])


def composite(
    source: Element, backdrop: Element, operator: Operator = CompositeOperator.OVER,
    *, k: Sequence[float] = (), scale: float | None = None,
) -> Image:
    """Composite two elements into a new ``<image>`` (see :meth:`Compositing.composite`).

    Parameters
    ----------
    source : Element
        The element drawn on top: an image or any drawable element.
    backdrop : Element
        What lies underneath.
    operator : CompositeOperator, BlendMode or str, optional
        An ``feComposite`` operator or ``feBlend`` mode. Defaults to ``CompositeOperator.OVER``.
    k : sequence of float, optional
        ``(k1, k2, k3, k4)`` for ``"arithmetic"``. Defaults to ().
    scale : float, optional
        Pixels per user unit of the result. Defaults to None, which uses the
        finer resolution of the images involved (1 for other elements).

    Returns
    -------
    Image
        A new image; both operands are left unchanged.

    Raises
    ------
    ValueError
        If the operator is unknown.
    TypeError
        If an operand has no known size.

    See Also
    --------
    Compositing.composite : The same as a method.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> from svgwriter.elements.structure._compositing import composite
    >>> red = svg.Image(np.array([[[1.0, 0, 0]]]), alpha=0.5)
    >>> blue = svg.Image(np.array([[[0, 0, 1.0]]]))
    >>> composite(red, blue).rgba().round(2).tolist()
    [[[0.5, 0.0, 0.5, 1.0]]]
    """
    from ...ops.composite import composite_rgba, resolve_operator
    from .._convert import render_box
    from ._image import Image

    op = resolve_operator(operator)
    if scale is None and _same_raster(source, backdrop):
        result: Image = source.clone()  # type: ignore[assignment]
        result.attributes["xlink:href"] = result.pixels.composite(backdrop.pixels, op, k=k)  # type: ignore[union-attr]
        return result
    box = _canvas(source, backdrop, op)
    densities = [d for d in (_density(source), _density(backdrop)) if d is not None]
    scale = scale if scale is not None else max(densities, default=DEFAULT_SCALE)
    rgba = composite_rgba(render_box(source, box, scale), render_box(backdrop, box, scale), op, k=k)
    return Image(rgba, box.x, box.y, box.width, box.height)


class Compositing:
    """Porter-Duff operators on placed images.

    ``a | b`` is *a* over *b*, ``a & b`` is *a* in *b* (masked by *b*'s
    alpha), ``a - b`` is *a* out of *b*, and ``a ^ b`` is the xor: the
    same areas as the boolean operators on shapes. ``a * b`` is the
    ``multiply`` blend. The other operand can be any drawable element,
    which is rasterized at the image's resolution. With numbers and
    offsets the operators keep their transform meaning (``img * 2``,
    ``img - (dx, dy)``), and ``a + b`` still groups.

    See Also
    --------
    Compositing.composite : The same operators with an explicit operator, mode and scale.
    svgwriter.elements.structure.Pixels.composite : Composite raw pixel arrays.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> red = svg.Image(np.array([[[1.0, 0, 0]]]), alpha=0.5)
    >>> blue = svg.Image(np.array([[[0, 0, 1.0]]]))
    >>> (red | blue).rgba().round(2).tolist()
    [[[0.5, 0.0, 0.5, 1.0]]]
    >>> (red - blue).alpha.round(2).tolist()
    [[[0.0]]]
    """

    def composite(
        self, backdrop: Element, operator: Operator = CompositeOperator.OVER,
        *, k: Sequence[float] = (), scale: float | None = None,
    ) -> Image:
        """Composite this element onto *backdrop* into a new ``<image>``.

        Images with the same placement and pixel size are combined pixel for
        pixel. Otherwise both are rendered onto one canvas in parent
        coordinates: the union of their bounds, or the source's bounds for
        ``in`` and ``out`` and the backdrop's for ``atop``.

        Parameters
        ----------
        backdrop : Element
            What lies underneath: an image or any drawable element.
        operator : CompositeOperator, BlendMode or str, optional
            An ``feComposite`` operator (``"over"``, ``"in"``, ``"out"``,
            ``"atop"``, ``"xor"``, ``"arithmetic"``) or an ``feBlend`` mode
            (``"multiply"``, ``"screen"``, ``"darken"``, ``"lighten"``,
            ``"normal"``). Defaults to ``"over"``.
        k : sequence of float, optional
            ``(k1, k2, k3, k4)`` for ``"arithmetic"``. Defaults to ().
        scale : float, optional
            Pixels per user unit of the result; defaults to the finer
            resolution of the images involved (1 for other elements).

        Returns
        -------
        Image
            A new image; both operands are left unchanged.

        Raises
        ------
        ValueError
            If the operator is unknown.
        TypeError
            If an operand has no known size.

        See Also
        --------
        svgwriter.ops.composite_rgba : The same on raw RGBA arrays.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> red = svg.Image(np.array([[[1.0, 0, 0]]]), alpha=0.5)
        >>> blue = svg.Image(np.array([[[0, 0, 1.0]]]))
        >>> (red | blue).rgba().round(2).tolist()
        [[[0.5, 0.0, 0.5, 1.0]]]
        >>> red.composite(blue, "multiply").rgba().round(2).tolist()
        [[[0.0, 0.0, 0.5, 1.0]]]
        >>> photo = svg.Image(np.ones((20, 20, 3)))
        >>> bool((photo & svg.circle(10, 10, 10)).alpha[0, 0, 0] < 0.5)
        True
        """
        return composite(self, backdrop, operator, k=k, scale=scale)  # type: ignore[arg-type]

    def _pair(self, other: Any, operator: CompositeOperator, reflected: bool = False) -> Any:
        if not isinstance(other, Element):
            return NotImplemented
        return composite(other, self, operator) if reflected else composite(self, other, operator)  # type: ignore[arg-type]

    def __or__(self, other: Any) -> Any:
        return self._pair(other, CompositeOperator.OVER)

    def __ror__(self, other: Any) -> Any:
        return self._pair(other, CompositeOperator.OVER, reflected=True)

    def __and__(self, other: Any) -> Any:
        return self._pair(other, CompositeOperator.IN)

    def __rand__(self, other: Any) -> Any:
        return self._pair(other, CompositeOperator.IN, reflected=True)

    def __xor__(self, other: Any) -> Any:
        return self._pair(other, CompositeOperator.XOR)

    def __rxor__(self, other: Any) -> Any:
        return self._pair(other, CompositeOperator.XOR, reflected=True)

    def __sub__(self, other: Any) -> Any:
        """``img - other`` keeps the image outside *other*; ``img - (dx, dy)`` translates a copy."""
        if isinstance(other, Element):
            return composite(self, other, CompositeOperator.OUT)  # type: ignore[arg-type]
        return super().__sub__(other)  # type: ignore[misc]

    def __mul__(self, other: Any) -> Any:
        """``img * other`` is the ``multiply`` blend; ``img * k`` scales a copy."""
        if isinstance(other, Element):
            return composite(self, other, BlendMode.MULTIPLY)  # type: ignore[arg-type]
        return super().__mul__(other)  # type: ignore[misc]

    def __rmul__(self, other: Any) -> Any:
        if isinstance(other, Element):
            return composite(other, self, BlendMode.MULTIPLY)  # type: ignore[arg-type]
        return super().__rmul__(other)  # type: ignore[misc]

    def __rsub__(self, other: Any) -> Any:
        return self._pair(other, CompositeOperator.OUT, reflected=True)
