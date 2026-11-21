"""
``Frame``: the base of layout groups (padding, size, background, lazy arranging) and ``settle``.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, ClassVar, Literal, overload

from ..attributes.cascade import frozen_rules
from ..elements import Group, Rect, Use
from ..elements.core import Child, Element
from ..pathdata.data import BBox, PathData
from ..transform.matrix import Matrix
from ._constants import TOLERANCE
from ._lengths import Edges, LayoutLength, PaddingLike, edges, resolve, user_scale
from ._measure import extent, move, resizable, resize

__all__ = ["Frame", "settle"]

_DONE: ContextVar[set[int] | None] = ContextVar("svgwriter_layout_pass", default=None)


@contextmanager
def _layout_pass() -> Generator[set[int], None, None]:
    """One pass in which each layout group arranges at most once (joins an open pass)."""
    done = _DONE.get()
    if done is not None:
        yield done
        return
    token = _DONE.set(set())
    try:
        with frozen_rules():
            yield _DONE.get()  # type: ignore[misc]
    finally:
        _DONE.reset(token)


def settle(root: Element) -> None:
    """Arrange every layout group under *root* (included) now.

    Output (strings, files, rendering and every exporter) calls this, and a group arranges itself
    whenever it or one of its children is measured, so calling it is only needed to read
    children's transforms (``child.t``) directly.

    Parameters
    ----------
    root : Element
        The tree to arrange.

    Examples
    --------
    >>> import svgwriter as svg
    >>> a, b = svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 10)
    >>> stack = svg.VStack(a, b, gap=5)
    >>> svg.layout.settle(stack)
    >>> b.t.apply(0, 0)
    Point(x=0.0, y=15.0)
    """
    if not Frame.made:
        return
    with _layout_pass():
        for element in root.iter():
            if isinstance(element, Frame):
                element.arrange()


class Frame(Group):
    """A ``<g>`` that places its children itself; the base of :class:`VStack`, :class:`HStack` and :class:`Grid`.

    The frame's box starts at its local origin and is sized by its content plus padding, unless
    `width` or `height` fix it. Children are moved with transforms (and stretched children
    resized), so the output is plain SVG. Arranging is lazy: it runs when the frame or a child is
    measured and before any output, and never on attribute writes.

    Parameters
    ----------
    *children : Element
        The content, in order.
    padding : length or sequence of lengths, optional
        Space inside the edges, like CSS: one length, ``(vertical, horizontal)`` or
        ``(top, right, bottom, left)``. Defaults to 0.
    width, height : length, optional
        Fixed outer size; None sizes the frame to its content. Defaults to None.
    background : Element or str, optional
        A shape sized to the frame and drawn behind the children, or a theme role name for a
        plain rect in that role. Defaults to None.
    **kwargs
        Presentation, core and other ``<g>`` attributes in Python spelling.

    Notes
    -----
    Lengths are numbers of user units, or lengths with units (``"2mm"``, ``svg.mm(2)``). In a
    document whose ``viewBox`` counts in a physical unit (``Document(size="a4")``), lengths with
    units convert to that unit, so ``gap=svg.mm(2)`` is 2 mm on paper.

    Examples
    --------
    >>> import svgwriter as svg
    >>> card = svg.VStack(svg.rect(0, 0, 40, 10), padding=(4, 8), background="surface")
    >>> card.bounds()
    BBox(x=0.0, y=0.0, width=56.0, height=18.0)
    """

    arranges_children: ClassVar[bool] = True
    made: ClassVar[bool] = False
    _size: tuple[float, float] = (0.0, 0.0)
    _arranging: bool = False
    _background_child: Element | None = None
    _stretched: tuple[float | None, float | None] = (None, None)

    def __init__(
        self,
        *children: Child,
        padding: PaddingLike = 0,
        width: LayoutLength | None = None,
        height: LayoutLength | None = None,
        background: Element | str | None = None,
        **kwargs: Any,
    ) -> None:
        Frame.made = True
        super().__init__(*children, **kwargs)
        edges(padding)
        self._padding = padding
        self._width = width
        self._height = height
        self.background = background

    @property
    def padding(self) -> PaddingLike:
        """Space inside the edges: one length, ``(vertical, horizontal)`` or ``(top, right, bottom, left)``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> box = svg.VStack(svg.rect(0, 0, 10, 10))
        >>> box.padding = (2, 4)
        >>> box.bounds().width
        18.0
        """
        return self._padding

    @padding.setter
    def padding(self, value: PaddingLike) -> None:
        edges(value)
        self._padding = value

    @property
    def width(self) -> LayoutLength | None:
        """Fixed outer width, or None to fit the content.

        Examples
        --------
        >>> import svgwriter as svg
        >>> row = svg.HStack(svg.rect(0, 0, 10, 10))
        >>> row.width = 50
        >>> row.bounds().width
        50.0
        """
        return self._width

    @width.setter
    def width(self, value: LayoutLength | None) -> None:
        self._width = value

    @property
    def height(self) -> LayoutLength | None:
        """Fixed outer height, or None to fit the content.

        Examples
        --------
        >>> import svgwriter as svg
        >>> column = svg.VStack(svg.rect(0, 0, 10, 10), height=40)
        >>> column.bounds().height
        40.0
        """
        return self._height

    @height.setter
    def height(self, value: LayoutLength | None) -> None:
        self._height = value

    @property
    def background(self) -> Element | None:
        """The shape behind the children, sized to the frame; assign a shape, a role name or None.

        A rect or image takes the frame's size; any other shape is scaled to fill it.

        Examples
        --------
        >>> import svgwriter as svg
        >>> card = svg.VStack(svg.rect(0, 0, 30, 10), padding=5)
        >>> card.background = svg.rect(rx=4, fill="white")
        >>> card.background.bounds()
        BBox(x=0.0, y=0.0, width=40.0, height=20.0)
        """
        child = self._background_child
        return child if child is not None and child.parent is self else None

    @background.setter
    def background(self, value: Element | str | None) -> None:
        old = self.background
        if old is not None:
            self.remove(old)
        if isinstance(value, str):
            value = Rect().as_role(value)
        self._background_child = value
        if value is not None:
            self.insert(0, value)

    @property
    def _stretch(self) -> tuple[float | None, float | None]:
        return self._stretched

    @_stretch.setter
    def _stretch(self, value: tuple[float | None, float | None]) -> None:
        if value != self._stretched:
            self._stretched = value
            done = _DONE.get()
            if done is not None:
                done.discard(id(self))

    def arrange(self) -> Frame:
        """Place the children now (it also happens on its own before any measuring or output).

        Returns
        -------
        Frame
            This frame.

        Examples
        --------
        >>> import svgwriter as svg
        >>> a, b = svg.rect(0, 0, 10, 4), svg.rect(0, 0, 10, 4)
        >>> _ = svg.HStack(a, b, gap=2).arrange()
        >>> b.t.apply(0, 0)
        Point(x=12.0, y=0.0)
        """
        if self._arranging:
            return self
        if _DONE.get() is None:
            top: Element = self
            while top.parent is not None and top.parent.arranges_children:
                top = top.parent
            if top is not self:
                with _layout_pass():
                    top.arrange()  # type: ignore[attr-defined]
                    return self.arrange()
        with _layout_pass() as done:
            if id(self) in done:
                return self
            self._arranging = True
            try:
                self._arrange_now()
            finally:
                self._arranging = False
            done.add(id(self))
        return self

    def _arrange_now(self) -> None:
        scale = user_scale(self)
        pad = edges(self._padding, scale)
        outer = [self._stretched[axis] if self._stretched[axis] is not None
                 else None if fixed is None else resolve(fixed, scale)
                 for axis, fixed in enumerate((self._width, self._height))]
        inner = [None if side is None else max(side - extra, 0.0)
                 for side, extra in zip(outer, (pad.horizontal, pad.vertical), strict=True)]
        background = self.background
        items = [child for child in self.children if isinstance(child, Element) and child is not background]
        content = self._place(items, inner[0], inner[1], pad, scale)
        self._size = (outer[0] if outer[0] is not None else content[0] + pad.horizontal,
                      outer[1] if outer[1] is not None else content[1] + pad.vertical)
        if background is not None:
            self._fit_background(background)
        for child in items:
            if isinstance(child, Frame):
                child.arrange()

    def _place(self, items: list[Element], width: float | None, height: float | None, pad: Edges,
               scale: float) -> tuple[float, float]:
        """Place *items* in the content box and return its size; subclasses implement the layout."""
        raise NotImplementedError

    def _fit_background(self, background: Element) -> None:
        width, height = self._size
        if resizable(background):
            box = extent(background)
            if box is not None:
                resize(background, box, width, height)
                move(background, BBox(box.x, box.y, width, height), 0.0, 0.0)
            return
        local = background.local_bbox() if hasattr(background, "local_bbox") else None
        if local is None or local.width < TOLERANCE or local.height < TOLERANCE:
            return
        sx, sy = width / local.width, height / local.height
        background.t = Matrix(sx, 0.0, 0.0, sy, -local.x * sx, -local.y * sy)  # type: ignore[attr-defined]

    def local_bbox(self) -> BBox:
        """The frame's box: its local origin to its outer size.

        Returns
        -------
        BBox
            ``(0, 0, width, height)`` after arranging.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.HStack(svg.rect(0, 0, 10, 4), svg.rect(0, 0, 6, 8), padding=1).local_bbox()
        BBox(x=0.0, y=0.0, width=18.0, height=10.0)
        """
        self.arrange()
        return BBox(0.0, 0.0, *self._size)

    def local_outline(self) -> PathData:
        """Union of the arranged children's outlines.

        Returns
        -------
        PathData
            The combined outline.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.VStack(svg.rect(0, 0, 4, 4), svg.rect(0, 0, 4, 4), gap=2).local_outline().bbox
        BBox(x=0.0, y=0.0, width=4.0, height=10.0)
        """
        self.arrange()
        return super().local_outline()

    @overload
    def clone(self, linked: Literal[False] = False) -> Frame: ...

    @overload
    def clone(self, linked: Literal[True]) -> Use: ...

    def clone(self, linked: bool = False) -> Element:
        """A deep, detached copy that keeps the layout settings; see :meth:`Element.clone`.

        Parameters
        ----------
        linked : bool, optional
            Return a ``<use>`` of this frame instead. Defaults to False.

        Returns
        -------
        Element
            The copy, or a ``<use>``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> card = svg.VStack(svg.rect(0, 0, 10, 10), padding=2, background="surface")
        >>> twin = card.clone()
        >>> twin.background is twin.children[0], twin.bounds() == card.bounds()
        (True, True)
        """
        duplicate = super().clone(linked)  # type: ignore[call-overload]
        background = self.background
        if isinstance(duplicate, Frame) and background is not None:
            index = next(i for i, child in enumerate(self.children) if child is background)
            duplicate._background_child = duplicate.children[index]  # type: ignore[assignment]
        return duplicate  # type: ignore[no-any-return]

    copy = clone
    """Same as :meth:`clone`."""
