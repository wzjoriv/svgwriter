"""
Stacks: ``VStack``, ``HStack`` and the ``Spacer`` that fills their free space.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ..elements import Group
from ..elements.core import Child, Element
from ..pathdata.data import BBox
from ._constants import (
    ALIGN_SHARE,
    ALIGNMENTS,
    CENTER,
    DISTRIBUTIONS,
    END,
    SPACE_AROUND,
    SPACE_BETWEEN,
    SPACE_EVENLY,
    SPACER_GROW,
    STACK_ALIGN,
    START,
    STRETCH,
)
from ._frame import Frame
from ._lengths import Edges, LayoutLength, resolve
from ._measure import extent, move, release, resizable, resize

__all__ = ["HStack", "Spacer", "Stack", "VStack", "check_choice"]


def check_choice(value: str, choices: tuple[str, ...], what: str) -> str:
    """*value* if it is one of *choices*, else a ValueError naming them.

    Parameters
    ----------
    value : str
        The name given.
    choices : tuple of str
        The valid names.
    what : str
        What the name sets, for the message.

    Returns
    -------
    str
        `value`.

    Raises
    ------
    ValueError
        If `value` is not in `choices`.

    Examples
    --------
    >>> from svgwriter.layout._stack import check_choice
    >>> check_choice("end", ("start", "end"), "align")
    'end'
    """
    if value not in choices:
        raise ValueError(f"unknown {what} {value!r}; choose one of {', '.join(choices)}")
    return value


class Spacer(Group):
    """Flexible empty space in a stack: spacers share the free space along the main axis.

    Parameters
    ----------
    grow : float, optional
        This spacer's share relative to the other spacers. Defaults to 1.

    Notes
    -----
    A stack with spacers fills its fixed size, so its ``justify`` has nothing left to
    distribute. In the output a spacer is an empty ``<g/>``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> a, b = svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 10)
    >>> _ = svg.HStack(a, svg.Spacer(), b, width=100)
    >>> b.bounds().x
    90.0
    """

    def __init__(self, grow: float = SPACER_GROW, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.grow = grow

    @property
    def grow(self) -> float:
        """Share of the free space, relative to the other spacers.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Spacer(2).grow
        2.0
        """
        return self._grow

    @grow.setter
    def grow(self, value: float) -> None:
        if value < 0:
            raise ValueError(f"a spacer's grow cannot be negative, got {value}")
        self._grow = float(value)


def _distribution(justify: str, free: float, count: int) -> tuple[float, float]:
    """Leading space and extra space between items for *justify* (negative free space falls back like CSS)."""
    if free < 0 and justify in (SPACE_BETWEEN, SPACE_AROUND, SPACE_EVENLY):
        justify = START if justify == SPACE_BETWEEN else CENTER
    if justify == CENTER:
        return free / 2, 0.0
    if justify == END:
        return free, 0.0
    if justify == SPACE_BETWEEN:
        return 0.0, free / (count - 1) if count > 1 else 0.0
    if justify == SPACE_AROUND:
        return free / count / 2, free / count
    if justify == SPACE_EVENLY:
        return free / (count + 1), free / (count + 1)
    return 0.0, 0.0


class Stack(Frame):
    """Children in a row or column, with a gap, alignment across and distribution along the axis.

    Use :class:`VStack` or :class:`HStack`; see :class:`Frame` for `padding`, `width`, `height`
    and `background`.

    Parameters
    ----------
    *children : Element
        The content, in order; :class:`Spacer` children take the free space.
    gap : length, optional
        Space between neighbours. Defaults to 0.
    align : {"start", "center", "end", "stretch"}, optional
        Placement across the axis, like CSS ``align-items``. ``"stretch"`` resizes rects,
        images and layout groups to the stack's cross size; other children stay at the start.
        Defaults to ``"start"``.
    justify : {"start", "center", "end", "space_between", "space_around", "space_evenly"}, optional
        Distribution of free space along the axis when the stack is larger than its content,
        like CSS ``justify-content``. Defaults to ``"start"``.
    **kwargs
        `padding`, `width`, `height`, `background` and ``<g>`` attributes.

    Examples
    --------
    >>> import svgwriter as svg
    >>> row = svg.HStack(svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 4), gap=5, align="center")
    >>> row[1].bounds()
    BBox(x=15.0, y=3.0, width=10.0, height=4.0)
    """

    axis: ClassVar[int] = 0
    """0 lays children out left to right, 1 top to bottom."""

    def __init__(
        self,
        *children: Child,
        gap: LayoutLength = 0,
        align: str = STACK_ALIGN,
        justify: str = START,
        **kwargs: Any,
    ) -> None:
        self._gap = gap
        self.align_items = align
        self.justify_content = justify
        super().__init__(*children, **kwargs)

    @property
    def gap(self) -> LayoutLength:
        """Space between neighbouring children.

        Examples
        --------
        >>> import svgwriter as svg
        >>> column = svg.VStack(svg.rect(0, 0, 4, 4), svg.rect(0, 0, 4, 4))
        >>> column.gap = 6
        >>> column.bounds().height
        14.0
        """
        return self._gap

    @gap.setter
    def gap(self, value: LayoutLength) -> None:
        resolve(value)
        self._gap = value

    @property
    def align_items(self) -> str:
        """Placement across the axis (the `align` argument): start, center, end or stretch.

        Examples
        --------
        >>> import svgwriter as svg
        >>> column = svg.VStack(svg.rect(0, 0, 20, 4), svg.rect(0, 0, 10, 4))
        >>> column.align_items = "end"
        >>> column[1].bounds().x
        10.0
        """
        return self._align

    @align_items.setter
    def align_items(self, value: str) -> None:
        self._align = check_choice(value, ALIGNMENTS, "align")

    @property
    def justify_content(self) -> str:
        """Distribution along the axis (the `justify` argument).

        Examples
        --------
        >>> import svgwriter as svg
        >>> row = svg.HStack(svg.rect(0, 0, 10, 4), width=30)
        >>> row.justify_content = "center"
        >>> row[0].bounds().x
        10.0
        """
        return self._justify

    @justify_content.setter
    def justify_content(self, value: str) -> None:
        self._justify = check_choice(value, DISTRIBUTIONS, "justify")

    def _place(self, items: list[Element], width: float | None, height: float | None, pad: Edges,
               scale: float) -> tuple[float, float]:
        main, cross = self.axis, 1 - self.axis
        gap = resolve(self._gap, scale)
        entries: list[tuple[Element, BBox | None, float]] = []
        for child in items:
            if isinstance(child, Spacer):
                entries.append((child, None, child.grow))
                continue
            release(child)
            box = extent(child)
            if box is not None:
                entries.append((child, box, 0.0))
        sizes = [(box.width, box.height) if box is not None else (0.0, 0.0) for _, box, _ in entries]
        content = sum(size[main] for size in sizes) + gap * max(len(entries) - 1, 0)
        given = (width, height)
        along = given[main] if given[main] is not None else content
        across = given[cross] if given[cross] is not None else max((size[cross] for size in sizes), default=0.0)
        free = along - content
        growth = sum(grow for _, _, grow in entries)
        lead, extra = (0.0, 0.0) if growth else _distribution(self._justify, free, len(entries))
        origin = (pad.left, pad.top)
        cursor = origin[main] + lead
        share = ALIGN_SHARE[self._align]
        for (child, box, grow), size in zip(entries, sizes, strict=True):
            if box is None:
                cursor += max(free, 0.0) * grow / growth + gap + extra
                continue
            length, thickness = size[main], size[cross]
            if self._align == STRETCH and resizable(child):
                target = [None, None]
                target[cross] = across
                resize(child, box, *target)
                thickness = across
                box = BBox(box.x, box.y, *((length, across) if main == 0 else (across, length)))
            offset = origin[cross] + (across - thickness) * share
            move(child, box, *((cursor, offset) if main == 0 else (offset, cursor)))
            cursor += length + gap + extra
        return (along, across) if main == 0 else (across, along)


class HStack(Stack):
    """Children left to right; see :class:`Stack` for the arguments.

    Examples
    --------
    >>> import svgwriter as svg
    >>> row = svg.HStack(svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 10), gap=4, padding=2)
    >>> row.bounds(), row[1].bounds().x
    (BBox(x=0.0, y=0.0, width=28.0, height=14.0), 16.0)
    """

    axis: ClassVar[int] = 0


class VStack(Stack):
    """Children top to bottom; see :class:`Stack` for the arguments.

    Examples
    --------
    >>> import svgwriter as svg
    >>> card = svg.VStack(svg.text("Total", font_size=12), svg.rect(0, 0, 80, 20, rx=4),
    ...                   gap=6, padding=10, align="stretch", background="surface")
    >>> card.bounds().width, card[2].bounds().width
    (100.0, 80.0)
    """

    axis: ClassVar[int] = 1
