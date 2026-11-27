"""
Several runs of a text's characters picked together: ``text[[0, 3, 5]]``, a mask or ``text[::2]``.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any

from ._character import CharacterRange

if TYPE_CHECKING:
    from ...color.paint import PaintValue
    from ...units.length import LengthLike
    from ._text import Text

__all__ = ["CharacterSelection", "runs_of"]


def runs_of(positions: Sequence[int]) -> list[tuple[int, int]]:
    """Sorted, merged ``[first, last + 1)`` runs of character positions."""
    runs: list[tuple[int, int]] = []
    for position in sorted(set(positions)):
        if runs and runs[-1][1] == position:
            runs[-1] = (runs[-1][0], position + 1)
        else:
            runs.append((position, position + 1))
    return runs


class CharacterSelection:
    """Characters picked by a list, a mask or a stepped slice, as contiguous :class:`CharacterRange` runs.

    Setting a presentation attribute sets it on every run, so each run becomes a styled ``<tspan>``.

    Parameters
    ----------
    ranges : sequence of CharacterRange
        The runs, in text order.

    Examples
    --------
    >>> import svgwriter as svg
    >>> t = svg.text("Hello", x=0, y=20)
    >>> t[[0, 1, 4]].fill = "red"
    >>> str(t)
    '<text x="0" y="20"><tspan fill="red">He</tspan>ll<tspan fill="red">o</tspan></text>'
    >>> t[[True, False, True, False, True]].chars
    'Hlo'
    """

    __slots__ = ("ranges",)

    fill: PaintValue
    stroke: PaintValue
    stroke_width: LengthLike
    opacity: float
    fill_opacity: float
    stroke_opacity: float
    font_family: str
    font_size: LengthLike
    font_weight: str | int
    font_style: str
    text_decoration: str
    letter_spacing: LengthLike
    baseline_shift: LengthLike | str

    def __init__(self, ranges: Sequence[CharacterRange]) -> None:
        object.__setattr__(self, "ranges", tuple(ranges))

    @classmethod
    def of(cls, text: Text, positions: Sequence[int], bounds: Sequence[int]) -> CharacterSelection:
        """The selection of character *positions* (cluster indices) of *text*."""
        return cls([CharacterRange(text, bounds[start], bounds[stop]) for start, stop in runs_of(positions)])

    @property
    def chars(self) -> str:
        """The selected characters, in text order."""
        return "".join(run.chars for run in self.ranges)

    def __len__(self) -> int:
        return sum(len(run) for run in self.ranges)

    def __iter__(self) -> Iterator[CharacterRange]:
        return iter(self.ranges)

    def __setattr__(self, name: str, value: Any) -> None:
        for run in self.ranges:
            setattr(run, name, value)

    def effect(self, name: str, /, **options: Any) -> CharacterSelection:
        """Apply an effect from ``svg.effects`` to every run and return the selection."""
        for run in self.ranges:
            run.effect(name, **options)
        return self

    def __repr__(self) -> str:
        return f"CharacterSelection({self.chars!r}, runs={len(self.ranges)})"
