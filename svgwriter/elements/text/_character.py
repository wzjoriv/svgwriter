"""
``Character`` and ``CharacterRange``: live handles on characters of a ``<text>``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, NoReturn

from ...attributes.names import PRESENTATION_ATTRIBUTES, svg_name
from ._clusters import cluster_bounds
from ._textlayout import collect, number_list

if TYPE_CHECKING:
    from ...ops.text import GlyphBox
    from ...pathdata.data import BBox
    from ...transform.matrix import Point
    from ..shapes import Path
    from ._text import Text, TSpan

__all__ = ["Character", "CharacterRange"]


class _Characters:
    """Shared behaviour of the characters ``[start, stop)`` of a text."""

    __slots__ = ("start", "stop", "text")

    def __init__(self, text: Text, start: int, stop: int) -> None:
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "stop", stop)

    @property
    def chars(self) -> str:
        """The characters of the handle as a string.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.text("Hello", x=0, y=10)[1:4].chars
        'ell'
        """
        return self.text.characters[self.start:self.stop]

    def _boxes(self) -> list[GlyphBox]:
        return self.text.layout()[self.start:self.stop]

    def bounds(self) -> BBox | None:
        """Tight box of these characters in the text's parent coordinates.

        Returns
        -------
        BBox or None
            ``None`` when the characters have no outline (for example spaces).

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.text("Hi", x=0, y=20)[0].bounds() is not None
        True
        """
        from ...pathdata.data import PathData

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
        """Move only these characters, leaving the rest where they are.

        The move is written into the text's ``dx`` and ``dy`` lists, so the
        text stays selectable.

        Parameters
        ----------
        dx : float
            Horizontal shift in user units.
        dy : float, optional
            Vertical shift in user units. Defaults to 0.

        Returns
        -------
        Character or CharacterRange
            This handle, for chaining.

        Examples
        --------
        >>> import svgwriter as svg
        >>> t = svg.text("abc", x=0, y=10)
        >>> _ = t[1].translate(0, -4)
        >>> t.dy
        (0.0, -4.0, 4.0)
        """
        if self.start == self.stop:
            return self
        if dx:
            self._shift("dx", dx)
        if dy:
            self._shift("dy", dy)
        return self

    def rotate(self, degrees: float) -> Any:
        """Rotate each of these characters about its own baseline origin.

        The angle is added to the text's per-character ``rotate`` list.

        Parameters
        ----------
        degrees : float
            Rotation to add, clockwise in degrees.

        Returns
        -------
        Character or CharacterRange
            This handle, for chaining.

        Examples
        --------
        >>> import svgwriter as svg
        >>> t = svg.text("abc", x=0, y=10)
        >>> _ = t[1].rotate(20)
        >>> t.rotate_
        (0.0, 20.0, 0.0)
        """
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
        """Not supported: SVG text cannot scale part of a text.

        Raises
        ------
        TypeError
            Always; use :meth:`Text.glyphs` for outlines that can be scaled.

        See Also
        --------
        Character.to_path : One outline path for these characters.
        """
        self._unsupported("scale")

    def skew(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Not supported: SVG text cannot skew part of a text.

        Raises
        ------
        TypeError
            Always; use :meth:`Text.glyphs` for outlines that can be skewed.

        See Also
        --------
        Character.to_path : One outline path for these characters.
        """
        self._unsupported("skew")

    def to_path(self, **kwargs: Any) -> Path:
        """These characters' outlines as one ``<path>``.

        The path is styled like the first character's run and includes the
        text's transform.

        Parameters
        ----------
        **kwargs
            Attributes set on the resulting path.

        Returns
        -------
        Path
            The outline path.

        Examples
        --------
        >>> import svgwriter as svg
        >>> p = svg.text("Hi", x=0, y=20, fill="red")[0].to_path(stroke="blue")
        >>> p.get("fill"), p.get("stroke")
        ('red', 'blue')
        """
        from ...pathdata.data import PathData

        boxes = self._boxes()
        data = sum((b.placed() for b in boxes), PathData()).transformed(self.text.t)
        path = self.text._styled_path(data, boxes[0].source if boxes else None)
        path.update(**kwargs)
        return path

    def wrap(self, **attributes: Any) -> TSpan:
        """Wrap these characters in a ``<tspan>`` and return it.

        The characters are replaced in place by a span carrying *attributes*.

        Parameters
        ----------
        **attributes
            Attributes of the new :class:`TSpan`.

        Returns
        -------
        TSpan
            The new span.

        Raises
        ------
        ValueError
            When the range is empty or crosses existing ``<tspan>`` boundaries.

        Notes
        -----
        Collapsed whitespace inside the range is wrapped as written in the
        source, so it stays collapsed.

        Examples
        --------
        >>> import svgwriter as svg
        >>> t = svg.text("Hello world", x=0, y=20)
        >>> str(t[0:5].wrap(font_weight="bold"))
        '<tspan font-weight="bold">Hello</tspan>'
        """
        from ._text import TSpan

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


class Character(_Characters):
    """A live handle on character *index* of a ``<text>`` (``text[i]``).

    Parameters
    ----------
    text : Text
        The text the character belongs to.
    index : int
        Zero-based index into :attr:`Text.characters`.

    Notes
    -----
    Moves and rotations edit the text's ``dx``/``dy``/``rotate`` lists, so the
    result is still selectable SVG text. Scale and skew have no
    per-character form in SVG; use :meth:`Text.glyphs` for outlines that can
    be transformed freely.

    Examples
    --------
    >>> import svgwriter as svg
    >>> t = svg.text("abc", x=0, y=10)
    >>> t[1].translate(0, -4).rotate(20)
    Character('b', 1)
    >>> t.dy, t.rotate_
    ((0.0, -4.0, 4.0), (0.0, 20.0, 0.0))
    """

    __slots__ = ("_index",)

    def __init__(self, text: Text, index: int, start: int | None = None, stop: int | None = None) -> None:
        start = index if start is None else start
        super().__init__(text, start, start + 1 if stop is None else stop)
        object.__setattr__(self, "_index", index)

    @property
    def index(self) -> int:
        """Zero-based index of the character in the text.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.text("abc", x=0, y=10)[2].index
        2
        """
        return self._index

    def _where(self) -> str:
        return str(self.start)

    @property
    def char(self) -> str:
        """The character itself.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.text("abc", x=0, y=10)[1].char
        'b'
        """
        return self.text.characters[self.start:self.stop]

    @property
    def position(self) -> Point:
        """Baseline origin of the glyph in the text's local coordinates.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.text("abc", x=5, y=10)[0].position.y
        10.0
        """
        from ...transform.matrix import Point

        box = self._boxes()[0]
        return Point(box.x, box.y)

    @property
    def angle(self) -> float:
        """Per-character rotation in degrees.

        Examples
        --------
        >>> import svgwriter as svg
        >>> t = svg.text("abc", x=0, y=10)
        >>> _ = t[1].rotate(20)
        >>> t[1].angle
        20.0
        """
        return self._boxes()[0].angle

    def __repr__(self) -> str:
        return f"Character({self.char!r}, {self._index})"


class CharacterRange(_Characters):
    """A live handle on characters ``[start, stop)`` of a ``<text>`` (``text[a:b]``).

    Setting a presentation attribute on the range wraps it in a styled ``<tspan>``.

    Parameters
    ----------
    text : Text
        The text the characters belong to.
    start : int
        Index of the first character.
    stop : int
        Index one past the last character.

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

    def __iter__(self) -> Iterator[Character]:
        bounds = cluster_bounds(self.text.characters)
        return (Character(self.text, i, bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)
                if self.start <= bounds[i] < self.stop)

    def __repr__(self) -> str:
        return f"CharacterRange({self.chars!r}, {self.start}, {self.stop})"
