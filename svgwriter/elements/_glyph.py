"""``Glyph``: one character of a ``<text>``, positioned through SVG's per-character lists."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NoReturn

from ..attributes.length import Length, Unit

PERCENT = 100.0

if TYPE_CHECKING:
    from ..ops.text import GlyphBox
    from ..path.data import BBox
    from ..transform.matrix import Point
    from .shapes import Path
    from .text import Text

__all__ = ["Glyph", "number_list"]


def _units(value: Any, reference: float) -> float:
    length = Length.parse(value)
    if length.unit is Unit.PERCENT:
        return length.value * reference / PERCENT
    return length.to_user_units()


def number_list(value: Any, reference: float = 0.0) -> list[float]:
    """An SVG number or length list (``"1 2,3"``, a number or a sequence) as floats.

    Percentages resolve against *reference*.
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [_units(v, reference) for v in value]
    if isinstance(value, (int, float)):
        return [float(value)]
    return [_units(v, reference) for v in str(value).replace(",", " ").split()]


class Glyph:
    """A live handle on character *index* of a ``<text>``.

    Moves and rotations edit the text's ``dx``/``dy``/``rotate`` lists, so the
    result is still selectable SVG text. Other transforms (scale, skew) have
    no per-character form in SVG; use :meth:`Text.glyphs` for outlines that
    can be transformed freely.

    Examples
    --------
    >>> import svgwriter as svg
    >>> t = svg.text("abc", x=0, y=10)
    >>> t[1].translate(0, -4).rotate(20)
    Glyph('b', 1)
    >>> t.dy, t.rotate_
    ((0.0, -4.0, 4.0), (0.0, 20.0, 0.0))
    """

    __slots__ = ("index", "text")

    def __init__(self, text: Text, index: int) -> None:
        self.text = text
        self.index = index

    @property
    def char(self) -> str:
        return self.text.characters[self.index]

    def _box(self) -> GlyphBox:
        return self.text.layout()[self.index]

    @property
    def position(self) -> Point:
        """Baseline origin of the glyph in the text's local coordinates."""
        from ..transform.matrix import Point

        box = self._box()
        return Point(box.x, box.y)

    @property
    def angle(self) -> float:
        """Per-character rotation in degrees."""
        return self._box().angle

    def bounds(self) -> BBox | None:
        """Tight box of the placed glyph in the text's parent coordinates."""
        data = self._box().placed()
        return data.transformed(self.text.t).bbox if len(data) else None

    def _shift(self, name: str, amount: float) -> None:
        count = len(self.text.characters)
        values = number_list(self.text.get(name))
        values += [0.0] * (count - len(values))
        values[self.index] += amount
        if self.index + 1 < count:
            values[self.index + 1] -= amount
        while values and values[-1] == 0.0:
            values.pop()
        self.text.set(name, tuple(values) if values else None)

    def translate(self, dx: float, dy: float = 0.0) -> Glyph:
        """Move only this character (the others stay) and return the handle."""
        if dx:
            self._shift("dx", dx)
        if dy:
            self._shift("dy", dy)
        return self

    def rotate(self, degrees: float) -> Glyph:
        """Rotate only this character about its baseline origin and return the handle."""
        count = len(self.text.characters)
        given = number_list(self.text.get("rotate"))
        angles = [given[i] if i < len(given) else (given[-1] if given else 0.0) for i in range(count)]
        angles[self.index] += degrees
        while len(angles) > 1 and angles[-1] == angles[-2]:
            angles.pop()
        self.text.set("rotate", None if angles == [0.0] else tuple(angles))
        return self

    def _unsupported(self, operation: str) -> NoReturn:
        raise TypeError(
            f"SVG text cannot {operation} a single character; use text.glyphs()[{self.index}] "
            "for an outline path you can transform freely"
        )

    def scale(self, *args: Any, **kwargs: Any) -> NoReturn:
        self._unsupported("scale")

    def skew(self, *args: Any, **kwargs: Any) -> NoReturn:
        self._unsupported("skew")

    def to_path(self, **kwargs: Any) -> Path:
        """This character's outline as a ``<path>`` styled like the text."""
        path = self.text._styled_path(self._box().placed().transformed(self.text.t))
        path.update(**kwargs)
        return path

    def __repr__(self) -> str:
        return f"Glyph({self.char!r}, {self.index})"
