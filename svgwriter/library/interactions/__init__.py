"""
Ready-made interactions: ``el.interact.button()``, ``el.interact.highlight()``; add your own with
``@svg.preset.interaction``.

Interactions use hover styles and event-started SMIL only, so files stay plain SVG 1.1; still images, PDF and video
show the resting state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._internal._hover import add_hover_style
from ..._internal._presets import INTERACTIONS
from ._constants import HOVER_OPACITY, HOVER_STROKE_WIDTH, PRESS_OPACITY, PRESS_SECONDS

if TYPE_CHECKING:
    from ...model.elements.core import Element

__all__ = ["button", "highlight", "hover"]


@INTERACTIONS
def hover(element: Element, **properties: Any) -> None:
    """Style the element while the pointer is over it: ``el.interact.hover(fill="tomato", stroke_width=2)``.

    Written as a CSS ``:hover`` rule (``!important``, so theme roles and inline styles do not hide it); still
    images, PDF, video and office formats show the resting state. Calling it again adds to the hover style.

    Parameters
    ----------
    element : Element
        The element.
    **properties
        Presentation properties by Python name (``fill``, ``stroke``, ``stroke_width``, ``opacity``, ...).

    Raises
    ------
    ValueError
        If a name is not a presentation property (geometry cannot change on hover in SVG 1.1).

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(width=40, height=20)
    >>> _ = doc.rect(0, 0, 40, 20, id="b", fill="teal").interact.hover(fill="tomato")
    >>> "#b:hover { fill:tomato !important }" in doc.to_string()
    True
    """
    add_hover_style(element, **properties)


@INTERACTIONS
def button(element: Element, *, hover_opacity: float = HOVER_OPACITY, pressed_opacity: float = PRESS_OPACITY,
           press: float = PRESS_SECONDS) -> None:
    """Dim under the pointer and flash when pressed, like a push button.

    Parameters
    ----------
    element : Element
        The button.
    hover_opacity : float, optional
        Opacity while the pointer is over it. Defaults to 0.85.
    pressed_opacity : float, optional
        Opacity at the bottom of the press flash. Defaults to 0.6.
    press : float, optional
        Length of the press flash in seconds. Defaults to 0.15.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(width=60, height=30)
    >>> _ = doc.rect(5, 5, 50, 20, rx=6, fill="teal").interact.button()
    """
    add_hover_style(element, opacity=hover_opacity)
    element.animate.on("press").tween("opacity", 1, pressed_opacity, press, freeze=False)


@INTERACTIONS
def highlight(element: Element, *, color: str = "#f59e0b", width: float = HOVER_STROKE_WIDTH) -> None:
    """Outline the element in *color* while the pointer is over it.

    Parameters
    ----------
    element : Element
        The element to highlight.
    color : str, optional
        Outline colour. Defaults to amber.
    width : float, optional
        Outline width in user units. Defaults to 3.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(width=40, height=40)
    >>> _ = doc.circle(20, 20, 12, id="dot").interact.highlight(color="crimson")
    >>> "#dot:hover { stroke:crimson !important;stroke-width:3 !important }" in doc.to_string()
    True
    """
    add_hover_style(element, stroke=color, stroke_width=width)
