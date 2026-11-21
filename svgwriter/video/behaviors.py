"""Built-in behaviors: Python motion a :class:`~svgwriter.Scene` runs before every frame.

Each one starts from the element's :attr:`~svgwriter.Element.home` and moves it relative to that, about its
anchor, so it never drifts. Attach one by name (``element.animate.wiggle()``) or typed
(``scene.attach(element, wiggle, angle=10)``).

Example
-------
>>> import svgwriter as svg
>>> from svgwriter.video.behaviors import wiggle
>>> class Alarm(svg.Scene):
...     width, height, duration = 40, 40, 1.0
...     def build(self, doc):
...         self.bell = self.attach(doc.rect(10, 10, 20, 20), wiggle, angle=15)
>>> scene = Alarm()
>>> scene.update(0.0)
>>> scene.render(0.125)[:4]
b'\\x89PNG'
"""

from __future__ import annotations

import math

from .._internal._presets import BEHAVIORS
from ..model.elements import Transformable
from ._constants import (
    BREATHE_AMOUNT,
    BREATHE_PERIOD,
    HOVER_HEIGHT,
    HOVER_PERIOD,
    WIGGLE_ANGLE,
    WIGGLE_PERIOD,
)

__all__ = ["breathe", "hover", "wiggle"]


def _wave(seconds: float, period: float) -> float:
    return math.sin(math.tau * seconds / period)


def wiggle(element: Transformable, seconds: float, *, angle: float = WIGGLE_ANGLE,
           period: float = WIGGLE_PERIOD) -> None:
    """Rock back and forth by up to *angle* degrees about the anchor, once every *period* seconds.

    Parameters
    ----------
    element : Transformable
        The element to move.
    seconds : float
        The scene time.
    angle : float, optional
        Largest turn either way, in degrees. Defaults to 6.
    period : float, optional
        Seconds per full swing. Defaults to 0.5.

    Examples
    --------
    >>> import svgwriter as svg
    >>> class Bell(svg.Scene):
    ...     width, height, duration = 40, 40, 1.0
    ...     def build(self, doc):
    ...         self.bell = doc.rect(10, 10, 20, 20).animate.wiggle(angle=10, period=1).element
    >>> scene = Bell()
    >>> wiggle(scene.bell, 0.25, angle=10, period=1)
    >>> round(scene.bell.t.decompose()[2], 6)
    10.0
    """
    element.t = element.home.t
    element.rotate(angle * _wave(seconds, period))


def hover(element: Transformable, seconds: float, *, height: float = HOVER_HEIGHT,
          period: float = HOVER_PERIOD) -> None:
    """Float up and down by *height* user units, once every *period* seconds.

    Parameters
    ----------
    element : Transformable
        The element to move.
    seconds : float
        The scene time.
    height : float, optional
        Largest rise above home, in user units. Defaults to 4.
    period : float, optional
        Seconds per full rise and fall. Defaults to 2.

    Examples
    --------
    >>> import svgwriter as svg
    >>> class Balloon(svg.Scene):
    ...     width, height, duration = 40, 40, 2.0
    ...     def build(self, doc):
    ...         self.balloon = doc.circle(20, 20, 6).animate.hover().element
    >>> scene = Balloon()
    >>> hover(scene.balloon, 0.5)
    >>> scene.balloon.t.f
    -4.0
    """
    element.t = element.home.t
    element.translate(0.0, -height * _wave(seconds, period))


def breathe(element: Transformable, seconds: float, *, amount: float = BREATHE_AMOUNT,
            period: float = BREATHE_PERIOD) -> None:
    """Grow and shrink by the fraction *amount* about the anchor, once every *period* seconds.

    Parameters
    ----------
    element : Transformable
        The element to scale.
    seconds : float
        The scene time.
    amount : float, optional
        Largest change of size, as a fraction. Defaults to 0.05.
    period : float, optional
        Seconds per full breath. Defaults to 2.

    Examples
    --------
    >>> import svgwriter as svg
    >>> class Heart(svg.Scene):
    ...     width, height, duration = 40, 40, 2.0
    ...     def build(self, doc):
    ...         self.heart = doc.circle(20, 20, 10).animate.breathe(amount=0.5).element
    >>> scene = Heart()
    >>> breathe(scene.heart, 0.5, amount=0.5)
    >>> scene.heart.t.a
    1.5
    """
    element.t = element.home.t
    element.scale(1.0 + amount * _wave(seconds, period))


for _behavior in (wiggle, hover, breathe):
    BEHAVIORS.add_builtin(_behavior.__name__, _behavior)
