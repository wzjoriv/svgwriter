"""
TikZ node placement and labels: anchors, positions along a path and node options.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ._constants import ANCHORS, DIAGONAL, MARKUP_RE, SPACE_RE
from ._tikz_syntax import _options

if TYPE_CHECKING:
    from ._reading import RGB
    from ._tikz_syntax import Pair, Point

__all__: list[str] = []


@dataclass(frozen=True)
class _Place:
    """A named node or coordinate: its centre and, for shaped nodes, the half sizes of its border."""

    x: float
    y: float
    shape: str = "rectangle"
    half_width: float = 0.0
    half_height: float = 0.0

    def anchor(self, name: str) -> Point:
        """The border point at a compass anchor; diagonals of round shapes lie on the curve."""
        try:
            ux, uy = ANCHORS[name]
        except KeyError:
            raise ValueError(f"unknown anchor: {name!r}") from None
        scale = DIAGONAL if ux and uy and self.shape != "rectangle" else 1.0
        return self.x + ux * self.half_width * scale, self.y + uy * self.half_height * scale


@dataclass
class _Context:
    """What a picture shares between its commands: colours, styles and the nodes named so far."""

    colors: dict[str, RGB]
    styles: dict[str, list[Pair]]
    places: dict[str, _Place] = field(default_factory=dict)


def _read_node(tokens: list[tuple[str, str]], i: int, coordinate: bool) -> tuple[list[Pair], str, str | None, str | None, int]:
    """Options, name, ``at`` coordinate, text and the next index of the node starting at token *i*."""
    pairs: list[Pair] = []
    name, at, content = "", None, None
    while i < len(tokens):
        kind, body = tokens[i]
        if kind == "opts":
            pairs += _options(body)
        elif kind == "coord" and not name:
            name = body.strip()
        elif (kind, body) == ("op", "at") and i + 1 < len(tokens) and tokens[i + 1][0] == "coord":
            at, i = tokens[i + 1][1], i + 1
        elif kind == "text" and not coordinate:
            return pairs, name, at, body, i + 1
        else:
            break
        i += 1
    return pairs, name, at, content, i


def _plain(latex: str) -> str:
    r"""Node text without simple LaTeX markup: ``\textbf{x}`` keeps ``x``; ``\`` line breaks become spaces."""
    text = latex.replace("\\\\", " ")
    previous = None
    while previous != text:
        previous, text = text, MARKUP_RE.sub(r"\1", text)
    return SPACE_RE.sub(" ", text.replace("{", "").replace("}", "")).strip()
