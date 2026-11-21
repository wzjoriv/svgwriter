"""
Compositing primitives: blend, composite, merge, offset, flood, tile, image.
"""

from __future__ import annotations

from typing import Any

from ..._internal._enums import Keyword
from ..._internal._typing import Opacity
from ...attributes.viewbox import PreserveAspectRatio
from ...color.color import Color
from .._behavior import CoreAttributes, ExternalResourcesAttribute, XLinkAttributes
from ..core import Child, Container, ContentModel
from .base import FilterInput, FilterPrimitive, SingleInput, TwoInputs, remember_source, resolve_input

__all__ = [
    "BlendMode",
    "CompositeOperator",
    "FeBlend",
    "FeComposite",
    "FeFlood",
    "FeImage",
    "FeMerge",
    "FeMergeNode",
    "FeOffset",
    "FeTile",
]


class BlendMode(Keyword):
    """Blend modes of :class:`FeBlend`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.BlendMode.MULTIPLY.value
    'multiply'
    """

    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    DARKEN = "darken"
    LIGHTEN = "lighten"


class CompositeOperator(Keyword):
    """Operators of :class:`FeComposite`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.CompositeOperator.ATOP.value
    'atop'
    """

    OVER = "over"
    IN = "in"
    OUT = "out"
    ATOP = "atop"
    XOR = "xor"
    ARITHMETIC = "arithmetic"


class FeBlend(TwoInputs, tag="feBlend"):
    """``<feBlend>``: blend two inputs with a mode.

    Parameters
    ----------
    mode : BlendMode, optional
        How to blend. Defaults to ``BlendMode.NORMAL``, which is omitted from the output.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeBlend(svg.BlendMode.MULTIPLY, in_="SourceGraphic", in2="shade"))
    '<feBlend in="SourceGraphic" in2="shade" mode="multiply"/>'
    """

    def __init__(self, mode: BlendMode = BlendMode.NORMAL, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._assign(mode=None if mode is BlendMode.NORMAL else mode)


class FeComposite(TwoInputs, tag="feComposite"):
    """``<feComposite>``: Porter-Duff compositing or arithmetic.

    Parameters
    ----------
    operator : CompositeOperator, optional
        The compositing operation. Defaults to ``CompositeOperator.OVER``.
    k1, k2, k3, k4 : float, optional
        Coefficients of the ``arithmetic`` operator. Defaults to None.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeComposite(svg.CompositeOperator.IN))
    '<feComposite operator="in"/>'
    """

    def __init__(
        self,
        operator: CompositeOperator = CompositeOperator.OVER,
        *,
        k1: float | None = None,
        k2: float | None = None,
        k3: float | None = None,
        k4: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._assign(operator=operator, k1=k1, k2=k2, k3=k3, k4=k4)


class FeOffset(SingleInput, tag="feOffset"):
    """``<feOffset>``: shift the input.

    Parameters
    ----------
    dx, dy : float, optional
        Offset along each axis. Defaults to 0.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeOffset(dx=2, dy=3))
    '<feOffset dx="2" dy="3"/>'
    """

    def __init__(self, dx: float = 0, dy: float = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._assign(dx=dx, dy=dy)


class FeFlood(FilterPrimitive, tag="feFlood"):
    """``<feFlood>``: fill the sub-region with a color.

    Parameters
    ----------
    flood_color : Color or str, optional
        The fill color. Defaults to None.
    flood_opacity : float, optional
        Opacity in ``0..1``. Defaults to None.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeFlood("red", 0.5))
    '<feFlood flood-color="red" flood-opacity="0.5"/>'
    """

    def __init__(self, flood_color: Color | str | None = None, flood_opacity: Opacity | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._assign(flood_color=flood_color, flood_opacity=flood_opacity)


class FeTile(SingleInput, tag="feTile"):
    """``<feTile>``: repeat the input's sub-region.

    Parameters
    ----------
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeTile(in_="cell"))
    '<feTile in="cell"/>'
    """


class FeImage(XLinkAttributes, ExternalResourcesAttribute, FilterPrimitive, tag="feImage"):
    """``<feImage>``: an external image or referenced element as input.

    Parameters
    ----------
    href : str, optional
        URL of the image or reference to an element. Defaults to None.
    preserve_aspect_ratio : PreserveAspectRatio or str, optional
        How the image fits the sub-region. Defaults to None.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeImage("texture.png"))
    '<feImage xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="texture.png"/>'
    """

    def __init__(
        self,
        href: str | None = None,
        *,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(href=href, **kwargs)
        self._assign(preserve_aspect_ratio=preserve_aspect_ratio)


class FeMergeNode(CoreAttributes, tag="feMergeNode", content=ContentModel.ELEMENTS):
    """``<feMergeNode>``: one layer of ``feMerge``.

    Parameters
    ----------
    in_ : StandardInput, str or FilterPrimitive, optional
        The layer's input. Defaults to None.
    **kwargs
        Core and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeMergeNode("SourceGraphic"))
    '<feMergeNode in="SourceGraphic"/>'
    """

    def __init__(self, in_: FilterInput | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        remember_source(self, "in", in_)
        self._assign(in_=resolve_input(in_))


class FeMerge(FilterPrimitive, Container[FeMergeNode], tag="feMerge"):
    """``<feMerge>``: stack inputs with ``over``, first at the bottom.

    Parameters
    ----------
    *nodes : FeMergeNode, FilterInput
        Layers, either nodes or anything accepted as an input, which is
        wrapped in a node.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeMerge(svg.FeOffset(id="shadow"), "SourceGraphic"))
    '<feMerge><feMergeNode in="shadow-out"/><feMergeNode in="SourceGraphic"/></feMerge>'
    """

    def __init__(self, *nodes: Child | FilterInput, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        for node in nodes:
            self.add(node if isinstance(node, FeMergeNode) else FeMergeNode(node))  # type: ignore[arg-type]

    def _feed(self, source: FilterPrimitive) -> None:
        """``a >> merge`` adds *a* as the top layer."""
        self.add(FeMergeNode(source))
