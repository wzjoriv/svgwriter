"""
Stop building for gradients: ``add_stop``, ``from_colors`` and ``from_stops``.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any

from .._internal._typing import Opacity, Self
from ..color.color import Color
from ..pathdata.data import BBox

if TYPE_CHECKING:
    from .paint import Stop, StopSpec

__all__ = ["GradientStops"]


class GradientStops:
    """Adding stops and building gradients from colors; mixed into :class:`~svgwriter.elements.paint.Gradient`."""

    __slots__ = ()

    def _units_bbox(self, units_attribute: str) -> BBox | None:
        if str(self.get(units_attribute, "objectBoundingBox")) == "objectBoundingBox":
            return BBox(0.0, 0.0, 1.0, 1.0)
        return None

    def add_stop(self, offset: float, color: Color | str, opacity: Opacity | None = None, **kwargs: Any) -> Stop:
        """Append a color stop and return it.

        Parameters
        ----------
        offset : float
            Position along the gradient vector, 0 to 1.
        color : Color or str
            The stop color.
        opacity : float, optional
            The stop opacity. Defaults to None.
        **kwargs
            Further attributes of the :class:`Stop`.

        Returns
        -------
        Stop
            The new stop, already a child of the gradient.

        Examples
        --------
        >>> from svgwriter.elements.paint import LinearGradient
        >>> g = LinearGradient()
        >>> _ = g.add_stop(0, "red")
        >>> str(g)
        '<linearGradient><stop offset="0" stop-color="red"/></linearGradient>'
        """
        from .paint import Stop

        return self.add(Stop(offset, color, opacity, **kwargs))

    @classmethod
    def from_colors(cls, colors: Sequence[Color | str], **kwargs: Any) -> Self:
        """Create a gradient with evenly spaced stops.

        Parameters
        ----------
        colors : sequence of Color or str
            One color per stop, the first at offset 0 and the last at 1.
        **kwargs
            Attributes of the gradient.

        Returns
        -------
        Gradient
            A new gradient of the calling class.

        Examples
        --------
        >>> from svgwriter.elements.paint import LinearGradient
        >>> g = LinearGradient.from_colors(["red", "blue"])
        >>> [s.get("offset") for s in g]
        [0.0, 1.0]
        """
        gradient = cls(**kwargs)
        last = max(len(colors) - 1, 1)
        for index, color in enumerate(colors):
            gradient.add_stop(index / last, color)
        return gradient

    @classmethod
    def from_stops(cls, stops: Iterable[StopSpec], **kwargs: Any) -> Self:
        """Create a gradient from ``(offset, color)`` or ``(offset, color, opacity)`` tuples.

        Parameters
        ----------
        stops : iterable of tuple
            Stop specifications.
        **kwargs
            Attributes of the gradient.

        Returns
        -------
        Gradient
            A new gradient of the calling class.

        Examples
        --------
        >>> from svgwriter.elements.paint import LinearGradient
        >>> g = LinearGradient.from_stops([(0, "red"), (1, "blue", 0.5)])
        >>> len(g), g[1].get("stop-opacity")
        (2, 0.5)
        """
        gradient = cls(**kwargs)
        for spec in stops:
            gradient.add_stop(*spec)
        return gradient
