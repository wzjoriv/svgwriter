"""``Glyph`` and ``GlyphRange``: live handles on characters of a ``<text>``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, NoReturn

from ..attributes.names import PRESENTATION_ATTRIBUTES, svg_name
from ._textlayout import collect, number_list

if TYPE_CHECKING:
    from ..ops.text import GlyphBox
    from ..path.data import BBox
    from ..transform.matrix import Point
    from .shapes import Path
    from .text import Text, TSpan

__all__ = ["Glyph", "GlyphRange"]


class _Characters:
    """Shared behaviour of the characters ``[start, stop)`` of a text."""

    __slots__ = ("start", "stop", "text")

    def __init__(self, text: Text, start: int, stop: int) -> None:
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "stop", stop)

    @property
    def chars(self) -> str:
        return self.text.characters[self.start:self.stop]

    def _boxes(self) -> list[GlyphBox]:
        return self.text.layout()[self.start:self.stop]

    def bounds(self) -> BBox | None:
        """Tight box of these characters in the text's parent coordinates."""
        from ..path.data import PathData

        data = sum((b.placed() for b in self._boxes()), PathData())
        return data.transformed(self.text.t).bbox if len(data) else None

    def _shift(self, name: str, amount: float) -> None:
        count = len(self.text.characters)
        values = number_list(self.text.get(name))
        values += [0.0] * (count - len(values))
        values[self.start] += amount
        if self.stop < count:
            values[self.stop] -= amount
        while values and values[-1] == 0.0:
            values.pop()
        self.text.set(name, tuple(values) if values else None)

    def translate(self, dx: float, dy: float = 0.0) -> Any:
        """Move only these characters (the rest stay put) and return the handle."""
        if self.start == self.stop:
            return self
        if dx:
            self._shift("dx", dx)
        if dy:
            self._shift("dy", dy)
        return self

    def rotate(self, degrees: float) -> Any:
        """Rotate each of these characters about its own baseline origin and return the handle."""
        count = len(self.text.characters)
        given = number_list(self.text.get("rotate"))
        angles = [given[i] if i < len(given) else (given[-1] if given else 0.0) for i in range(count)]
        for index in range(self.start, self.stop):
            angles[index] += degrees
        while len(angles) > 1 and angles[-1] == angles[-2]:
            angles.pop()
        self.text.set("rotate", None if angles == [0.0] else tuple(angles))
        return self

    def _unsupported(self, operation: str) -> NoReturn:
        raise TypeError(
            f"SVG text cannot {operation} part of a text; use text.glyphs()[{self._where()}] "
            "for outline paths you can transform freely"
        )

    def _where(self) -> str:
        return f"{self.start}:{self.stop}"

    def scale(self, *args: Any, **kwargs: Any) -> NoReturn:
        self._unsupported("scale")

    def skew(self, *args: Any, **kwargs: Any) -> NoReturn:
        self._unsupported("skew")

    def to_path(self, **kwargs: Any) -> Path:
        """These characters' outlines as one ``<path>``, styled like the first one's run."""
        from ..path.data import PathData

        boxes = self._boxes()
        data = sum((b.placed() for b in boxes), PathData()).transformed(self.text.t)
        path = self.text._styled_path(data, boxes[0].source if boxes else None)
        path.update(**kwargs)
        return path

    def wrap(self, **attributes: Any) -> TSpan:
        """Wrap these characters in a ``<tspan>`` with *attributes* and return it.

        Raises
        ------
        ValueError
            When the range is empty or crosses existing ``<tspan>`` boundaries.

        Notes
        -----
        Collapsed whitespace inside the range is wrapped as written in the
        source, so it stays collapsed.
        """
        from .text import TSpan

        chars = collect(self.text)[self.start:self.stop]
        if not chars:
            raise ValueError("cannot wrap an empty range")
        first, last = chars[0], chars[-1]
        if first.chain != last.chain or first.child != last.child:
            raise ValueError("the range crosses existing <tspan> boundaries; wrap smaller pieces")
        owner = first.chain[0]
        string = owner.children[first.child]
        assert isinstance(string, str)
        span = TSpan(string[first.offset:last.offset + 1], **attributes)
        span.parent = owner
        pieces = [part for part in (string[:first.offset], span, string[last.offset + 1:]) if part]
        owner.children[first.child:first.child + 1] = pieces
        return span

    def __setattr__(self, name: str, value: Any) -> None:
        """``rng.fill = "red"`` (any presentation attribute) wraps the range in a styled ``<tspan>``."""
        if svg_name(name) in PRESENTATION_ATTRIBUTES:
            self.wrap(**{name: value})
            return
        raise AttributeError(f"{type(self).__name__} has no attribute {name!r}")


class Glyph(_Characters):
    """A live handle on character *index* of a ``<text>`` (``text[i]``).

    Moves and rotations edit the text's ``dx``/``dy``/``rotate`` lists, so the
    result is still selectable SVG text. Scale and skew have no
    per-character form in SVG; use :meth:`Text.glyphs` for outlines that can
    be transformed freely.

    Examples
    --------
    >>> import svgwriter as svg
    >>> t = svg.text("abc", x=0, y=10)
    >>> t[1].translate(0, -4).rotate(20)
    Glyph('b', 1)
    >>> t.dy, t.rotate_
    ((0.0, -4.0, 4.0), (0.0, 20.0, 0.0))
    """

    __slots__ = ()

    def __init__(self, text: Text, index: int) -> None:
        super().__init__(text, index, index + 1)

    @property
    def index(self) -> int:
        return self.start

    def _where(self) -> str:
        return str(self.start)

    @property
    def char(self) -> str:
        return self.text.characters[self.start]

    @property
    def position(self) -> Point:
        """Baseline origin of the glyph in the text's local coordinates."""
        from ..transform.matrix import Point

        box = self._boxes()[0]
        return Point(box.x, box.y)

    @property
    def angle(self) -> float:
        """Per-character rotation in degrees."""
        return self._boxes()[0].angle

    def __repr__(self) -> str:
        return f"Glyph({self.char!r}, {self.start})"


class GlyphRange(_Characters):
    """A live handle on characters ``[start, stop)`` of a ``<text>`` (``text[a:b]``).

    Examples
    --------
    >>> import svgwriter as svg
    >>> t = svg.text("Hello world", x=0, y=20)
    >>> t[6:11].fill = "red"
    >>> str(t)
    '<text x="0" y="20">Hello <tspan fill="red">world</tspan></text>'
    """

    __slots__ = ()

    def __len__(self) -> int:
        return self.stop - self.start

    def __iter__(self) -> Iterator[Glyph]:
        return (Glyph(self.text, i) for i in range(self.start, self.stop))

    def __repr__(self) -> str:
        return f"GlyphRange({self.chars!r}, {self.start}, {self.stop})"
