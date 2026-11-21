"""
``Grid``: children in rows and columns sized like CSS grid tracks.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import accumulate
from typing import Any, TypeVar

from ..elements.core import Child, Element
from ..pathdata.data import BBox
from ._constants import ALIGN_SHARE, ALIGNMENTS, GRID_ALIGN, STRETCH
from ._frame import Frame
from ._lengths import Edges, LayoutLength, pair
from ._measure import extent, move, release, resizable, resize
from ._stack import Spacer, check_choice
from ._tracks import TracksLike, auto_place, parse_tracks, size_tracks

__all__ = ["Grid"]

E = TypeVar("E", bound=Element)
SPAN = "_grid_span"


def _offsets(sizes: Sequence[float], start: float, gap: float) -> list[float]:
    return [start + before + gap * index for index, before in enumerate(accumulate([0.0, *sizes[:-1]]))]


class Grid(Frame):
    """Children in rows and columns, filled row by row.

    See :class:`Frame` for `padding`, `width`, `height` and `background`.

    Parameters
    ----------
    *children : Element
        The content, placed left to right then top to bottom; a :class:`Spacer` leaves a cell empty.
    columns : int, str or sequence
        A number of equal ``"1fr"`` columns, or one size per column: ``"auto"`` (fits its widest
        child), a length (fixed) or ``"Nfr"`` (a share of the free width), as a list or a
        space-separated string (``"auto 1fr 1fr"``).
    rows : int, str or sequence, optional
        Row sizes, written like `columns`. Rows past these, or all rows when None, are ``"1fr"``,
        so rows come out equal. Defaults to None.
    gap : length or (length, length), optional
        Space between cells: one length, or ``(column gap, row gap)``. Defaults to 0.
    align : {"start", "center", "end", "stretch"}, optional
        Vertical placement in each cell, like CSS ``align-items``. Defaults to ``"stretch"``.
    justify : {"start", "center", "end", "stretch"}, optional
        Horizontal placement in each cell, like CSS ``justify-items``. Defaults to ``"stretch"``.
    **kwargs
        `padding`, `width`, `height`, `background` and ``<g>`` attributes.

    Notes
    -----
    ``"stretch"`` resizes rects, images and layout groups to their cell; other children stay
    at the cell's start. Use :meth:`span` for children covering several cells.

    Examples
    --------
    >>> import svgwriter as svg
    >>> keys = [svg.rect(0, 0, 10, 10) for _ in range(6)]
    >>> pad = svg.Grid(*keys, columns=3, gap=2)
    >>> pad.bounds(), keys[4].bounds()
    (BBox(x=0.0, y=0.0, width=34.0, height=22.0), BBox(x=12.0, y=12.0, width=10.0, height=10.0))
    """

    def __init__(
        self,
        *children: Child,
        columns: TracksLike,
        rows: TracksLike | None = None,
        gap: LayoutLength | tuple[LayoutLength, LayoutLength] = 0,
        align: str = GRID_ALIGN,
        justify: str = GRID_ALIGN,
        **kwargs: Any,
    ) -> None:
        self.columns = columns
        self.rows = rows
        self.gap = gap
        self.align_items = align
        self.justify_items = justify
        super().__init__(*children, **kwargs)

    @property
    def columns(self) -> TracksLike:
        """The column count or sizes.

        Examples
        --------
        >>> import svgwriter as svg
        >>> grid = svg.Grid(*[svg.rect(0, 0, 10, 10) for _ in range(4)], columns=4)
        >>> grid.columns = 2
        >>> grid.bounds().height
        20.0
        """
        return self._columns

    @columns.setter
    def columns(self, value: TracksLike) -> None:
        if not parse_tracks(value):
            raise ValueError("a grid needs at least one column")
        self._columns = value

    @property
    def rows(self) -> TracksLike | None:
        """The row sizes, or None for equal rows as needed.

        Examples
        --------
        >>> import svgwriter as svg
        >>> grid = svg.Grid(svg.rect(0, 0, 10, 10), columns=1, rows=[30])
        >>> grid.bounds().height
        30.0
        """
        return self._rows

    @rows.setter
    def rows(self, value: TracksLike | None) -> None:
        parse_tracks(value)
        self._rows = value

    @property
    def gap(self) -> LayoutLength | tuple[LayoutLength, LayoutLength]:
        """Space between cells: one length or ``(column gap, row gap)``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> grid = svg.Grid(svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 10), columns=2)
        >>> grid.gap = (6, 0)
        >>> grid.bounds().width
        26.0
        """
        return self._gap

    @gap.setter
    def gap(self, value: LayoutLength | tuple[LayoutLength, LayoutLength]) -> None:
        pair(value)
        self._gap = value

    @property
    def align_items(self) -> str:
        """Vertical placement in each cell (the `align` argument).

        Examples
        --------
        >>> import svgwriter as svg
        >>> grid = svg.Grid(svg.rect(0, 0, 10, 4), columns=1, rows=[10])
        >>> grid.align_items = "end"
        >>> grid[0].bounds().y
        6.0
        """
        return self._align

    @align_items.setter
    def align_items(self, value: str) -> None:
        self._align = check_choice(value, ALIGNMENTS, "align")

    @property
    def justify_items(self) -> str:
        """Horizontal placement in each cell (the `justify` argument).

        Examples
        --------
        >>> import svgwriter as svg
        >>> grid = svg.Grid(svg.circle(0, 0, 2), columns=[10], justify="center")
        >>> grid[0].bounds().x
        3.0
        """
        return self._justify

    @justify_items.setter
    def justify_items(self, value: str) -> None:
        self._justify = check_choice(value, ALIGNMENTS, "justify")

    def span(self, child: E, columns: int = 1, rows: int = 1) -> E:
        """Let *child* cover *columns* by *rows* cells.

        Parameters
        ----------
        child : Element
            A child of this grid.
        columns, rows : int, optional
            Number of cells across and down. Defaults to 1.

        Returns
        -------
        Element
            `child`.

        Raises
        ------
        ValueError
            If `child` is not in this grid or a span is below one.

        Examples
        --------
        >>> import svgwriter as svg
        >>> zero, dot = svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 10)
        >>> grid = svg.Grid(zero, dot, columns=3, gap=2)
        >>> grid.span(zero, columns=2).bounds().width, dot.bounds().x
        (22.0, 24.0)
        """
        if child.parent is not self:
            raise ValueError(f"<{child.tag}> is not a child of this grid")
        if columns < 1 or rows < 1:
            raise ValueError(f"a span covers at least one cell, got {columns} x {rows}")
        object.__setattr__(child, SPAN, (int(columns), int(rows)))
        return child

    def _place(self, items: list[Element], width: float | None, height: float | None, pad: Edges,
               scale: float) -> tuple[float, float]:
        gaps = pair(self._gap, scale)
        columns = parse_tracks(self._columns, scale)
        placed: list[tuple[Element, BBox | None, tuple[int, int]]] = []
        for child in items:
            if not isinstance(child, Spacer):
                release(child)
                box = extent(child)
                if box is None:
                    continue
            else:
                box = None
            placed.append((child, box, child.__dict__.get(SPAN, (1, 1))))
        spans = [(min(wide, len(columns)), tall) for _, _, (wide, tall) in placed]
        cells = auto_place(spans, len(columns))
        rows = parse_tracks(self._rows, scale)
        needed = max((row + tall for (_, row), (_, tall) in zip(cells, spans, strict=True)), default=0)
        if needed > len(rows):
            rows += parse_tracks(needed - len(rows))
        sizes = []
        for axis, (tracks, available) in enumerate(((columns, width), (rows, height))):
            contents = [0.0] * len(tracks)
            spanning = []
            for (_, box, _), cell, span in zip(placed, cells, spans, strict=True):
                if box is None:
                    continue
                size = box.width if axis == 0 else box.height
                if span[axis] == 1:
                    contents[cell[axis]] = max(contents[cell[axis]], size)
                else:
                    spanning.append((cell[axis], span[axis], size))
            sizes.append(size_tracks(tracks, contents, spanning, available, gaps[axis]))
        starts = [_offsets(sizes[0], pad.left, gaps[0]), _offsets(sizes[1], pad.top, gaps[1])]
        for (child, box, _), cell, span in zip(placed, cells, spans, strict=True):
            if box is None:
                continue
            corner, extent_ = [], []
            for axis, mode in enumerate((self._justify, self._align)):
                first, count = cell[axis], span[axis]
                room = sum(sizes[axis][first:first + count]) + gaps[axis] * (count - 1)
                size = box.width if axis == 0 else box.height
                if mode == STRETCH and resizable(child):
                    size = room
                extent_.append(size)
                corner.append(starts[axis][first] + (room - size) * ALIGN_SHARE[mode])
            if (extent_[0], extent_[1]) != (box.width, box.height):
                resize(child, box, extent_[0] if extent_[0] != box.width else None,
                       extent_[1] if extent_[1] != box.height else None)
                box = BBox(box.x, box.y, extent_[0], extent_[1])
            move(child, box, corner[0], corner[1])
        content = [sum(axis_sizes) + gap * max(len(axis_sizes) - 1, 0) for axis_sizes, gap in zip(sizes, gaps, strict=True)]
        return (width if width is not None else content[0], height if height is not None else content[1])
