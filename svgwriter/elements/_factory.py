"""``ElementFactory``: ``doc.circle(...)``-style shortcuts.

Each shortcut builds one element from its arguments, adds it and returns
it. Shapes and text go to the insertion point; paint servers, clip paths,
masks, markers, filters and symbols go into ``<defs>`` with an id.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from .base import Element
    from .clip import ClipPath, Marker, Mask
    from .filters.base import Filter
    from .paint import LinearGradient, Pattern, RadialGradient
    from .shapes import Circle, Ellipse, Line, Path, Polygon, Polyline, Rect
    from .structure import A, Group, Image, Switch, Symbol, Use
    from .text import Text

__all__ = ["ElementFactory"]

E = TypeVar("E", bound="Element")


class ElementFactory:
    """Shortcut methods shared by :class:`~svgwriter.Document` and containers.

    Every shortcut takes exactly the arguments of the element class it is
    named after.

    See Also
    --------
    svgwriter.elements.container.GraphicsContainer : Containers that use these shortcuts.

    Examples
    --------
    >>> from svgwriter import Document
    >>> doc = Document(100, 100)
    >>> sky = doc.linear_gradient(x2=0, y2=1)
    >>> doc.rect(0, 0, 100, 100, fill=sky).get("fill") == sky.url
    True
    >>> sky.parent is doc.defs
    True
    """

    __slots__ = ()

    @abstractmethod
    def _place(self, element: E) -> E:
        """Add *element* at the insertion point and return it."""

    @abstractmethod
    def _define(self, element: E) -> E:
        """Add *element* to the applicable ``<defs>`` and return it."""

    def rect(self, *args: Any, **kwargs: Any) -> Rect:
        """Add a :class:`~svgwriter.Rect`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Rect`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Rect`.

        Returns
        -------
        Rect
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.rect(0, 0, 10, 10).tag
        'rect'
        """
        from .shapes import Rect

        return self._place(Rect(*args, **kwargs))

    def circle(self, *args: Any, **kwargs: Any) -> Circle:
        """Add a :class:`~svgwriter.Circle`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Circle`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Circle`.

        Returns
        -------
        Circle
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.circle(5, 5, 2).tag
        'circle'
        """
        from .shapes import Circle

        return self._place(Circle(*args, **kwargs))

    def ellipse(self, *args: Any, **kwargs: Any) -> Ellipse:
        """Add an :class:`~svgwriter.Ellipse`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Ellipse`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Ellipse`.

        Returns
        -------
        Ellipse
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.ellipse(5, 5, 3, 2).tag
        'ellipse'
        """
        from .shapes import Ellipse

        return self._place(Ellipse(*args, **kwargs))

    def line(self, *args: Any, **kwargs: Any) -> Line:
        """Add a :class:`~svgwriter.Line`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Line`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Line`.

        Returns
        -------
        Line
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.line(0, 0, 5, 5).tag
        'line'
        """
        from .shapes import Line

        return self._place(Line(*args, **kwargs))

    def polyline(self, *args: Any, **kwargs: Any) -> Polyline:
        """Add a :class:`~svgwriter.Polyline`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Polyline`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Polyline`.

        Returns
        -------
        Polyline
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.polyline([(0, 0), (5, 5)]).tag
        'polyline'
        """
        from .shapes import Polyline

        return self._place(Polyline(*args, **kwargs))

    def polygon(self, *args: Any, **kwargs: Any) -> Polygon:
        """Add a :class:`~svgwriter.Polygon`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Polygon`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Polygon`.

        Returns
        -------
        Polygon
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.polygon([(0, 0), (5, 0), (5, 5)]).tag
        'polygon'
        """
        from .shapes import Polygon

        return self._place(Polygon(*args, **kwargs))

    def path(self, *args: Any, **kwargs: Any) -> Path:
        """Add a :class:`~svgwriter.Path`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Path`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Path`.

        Returns
        -------
        Path
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.path("M0 0 L5 5").tag
        'path'
        """
        from .shapes import Path

        return self._place(Path(*args, **kwargs))

    def text(self, *args: Any, **kwargs: Any) -> Text:
        """Add a :class:`~svgwriter.Text`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Text`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Text`.

        Returns
        -------
        Text
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.text("hi").tag
        'text'
        """
        from .text import Text

        return self._place(Text(*args, **kwargs))

    def group(self, *args: Any, **kwargs: Any) -> Group:
        """Add a :class:`~svgwriter.Group`; use it in ``with`` to nest.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Group`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Group`.

        Returns
        -------
        Group
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.group().tag
        'g'
        """
        from .structure import Group

        return self._place(Group(*args, **kwargs))

    def link(self, *args: Any, **kwargs: Any) -> A:
        """Add an ``<a>`` (:class:`~svgwriter.A`).

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.A`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.A`.

        Returns
        -------
        A
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.link(href="#a").tag
        'a'
        """
        from .structure import A

        return self._place(A(*args, **kwargs))

    def switch(self, *args: Any, **kwargs: Any) -> Switch:
        """Add a :class:`~svgwriter.Switch`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Switch`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Switch`.

        Returns
        -------
        Switch
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.switch().tag
        'switch'
        """
        from .structure import Switch

        return self._place(Switch(*args, **kwargs))

    def use(self, *args: Any, **kwargs: Any) -> Use:
        """Add a :class:`~svgwriter.Use`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Use`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Use`.

        Returns
        -------
        Use
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.use("#a").tag
        'use'
        """
        from .structure import Use

        return self._place(Use(*args, **kwargs))

    def image(self, *args: Any, **kwargs: Any) -> Image:
        """Add an :class:`~svgwriter.Image`.

        Builds the element from the arguments and adds it at the insertion point.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Image`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Image`.

        Returns
        -------
        Image
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.image("a.png", width=5, height=5).tag
        'image'
        """
        from .structure import Image

        return self._place(Image(*args, **kwargs))

    def linear_gradient(self, *args: Any, **kwargs: Any) -> LinearGradient:
        """Define a :class:`~svgwriter.LinearGradient` in ``<defs>``.

        Builds the element from the arguments, gives it an id and adds it to
        the applicable ``<defs>``.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.LinearGradient`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.LinearGradient`.

        Returns
        -------
        LinearGradient
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.linear_gradient().parent.tag
        'defs'
        """
        from .paint import LinearGradient

        return self._define(LinearGradient(*args, **kwargs))

    def radial_gradient(self, *args: Any, **kwargs: Any) -> RadialGradient:
        """Define a :class:`~svgwriter.RadialGradient` in ``<defs>``.

        Builds the element from the arguments, gives it an id and adds it to
        the applicable ``<defs>``.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.RadialGradient`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.RadialGradient`.

        Returns
        -------
        RadialGradient
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.radial_gradient().parent.tag
        'defs'
        """
        from .paint import RadialGradient

        return self._define(RadialGradient(*args, **kwargs))

    def pattern(self, *args: Any, **kwargs: Any) -> Pattern:
        """Define a :class:`~svgwriter.Pattern` in ``<defs>``.

        Builds the element from the arguments, gives it an id and adds it to
        the applicable ``<defs>``.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Pattern`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Pattern`.

        Returns
        -------
        Pattern
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.pattern().parent.tag
        'defs'
        """
        from .paint import Pattern

        return self._define(Pattern(*args, **kwargs))

    def clip_path(self, *args: Any, **kwargs: Any) -> ClipPath:
        """Define a :class:`~svgwriter.ClipPath` in ``<defs>``.

        Builds the element from the arguments, gives it an id and adds it to
        the applicable ``<defs>``.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.ClipPath`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.ClipPath`.

        Returns
        -------
        ClipPath
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.clip_path().parent.tag
        'defs'
        """
        from .clip import ClipPath

        return self._define(ClipPath(*args, **kwargs))

    def mask(self, *args: Any, **kwargs: Any) -> Mask:
        """Define a :class:`~svgwriter.Mask` in ``<defs>``.

        Builds the element from the arguments, gives it an id and adds it to
        the applicable ``<defs>``.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Mask`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Mask`.

        Returns
        -------
        Mask
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.mask().parent.tag
        'defs'
        """
        from .clip import Mask

        return self._define(Mask(*args, **kwargs))

    def marker(self, *args: Any, **kwargs: Any) -> Marker:
        """Define a :class:`~svgwriter.Marker` in ``<defs>``.

        Builds the element from the arguments, gives it an id and adds it to
        the applicable ``<defs>``.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Marker`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Marker`.

        Returns
        -------
        Marker
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.marker().parent.tag
        'defs'
        """
        from .clip import Marker

        return self._define(Marker(*args, **kwargs))

    def filter(self, *args: Any, **kwargs: Any) -> Filter:
        """Define a :class:`~svgwriter.Filter` in ``<defs>``.

        Builds the element from the arguments, gives it an id and adds it to
        the applicable ``<defs>``.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Filter`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Filter`.

        Returns
        -------
        Filter
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.filter().parent.tag
        'defs'
        """
        from .filters.base import Filter

        return self._define(Filter(*args, **kwargs))

    def symbol(self, *args: Any, **kwargs: Any) -> Symbol:
        """Define a :class:`~svgwriter.Symbol` in ``<defs>``.

        Builds the element from the arguments, gives it an id and adds it to
        the applicable ``<defs>``.

        Parameters
        ----------
        *args
            Positional arguments of :class:`~svgwriter.Symbol`.
        **kwargs
            Keyword arguments of :class:`~svgwriter.Symbol`.

        Returns
        -------
        Symbol
            The new element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.symbol().parent.tag
        'defs'
        """
        from .structure import Symbol

        return self._define(Symbol(*args, **kwargs))
