"""Text layout across ``<text>`` and nested ``<tspan>`` runs, following SVG 1.1's text rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from ..attributes.cascade import Rule, computed, rules_of
from ..attributes.length import Length, Unit

if TYPE_CHECKING:
    from ..ops.text import GlyphBox
    from .base import Element

__all__ = ["Char", "collect", "layout", "number_list"]

POSITIONING: Final = ("x", "y", "dx", "dy", "rotate")
PERCENT: Final = 100.0
DEFAULT_FONT_FAMILY: Final = "sans-serif"
DEFAULT_FONT_SIZE: Final = 16.0
FONT_WEIGHTS: Final = {"normal": 400, "bold": 700, "bolder": 700, "lighter": 300}
FONT_SIZE_KEYWORDS: Final = {"xx-small": 9.0, "x-small": 10.0, "small": 13.0, "medium": 16.0, "large": 18.0,
                             "x-large": 24.0, "xx-large": 32.0, "smaller": 13.0, "larger": 19.0}
_PRESERVE: Final = {10: " ", 13: " ", 9: " "}
_DEFAULT: Final = {10: None, 13: None, 9: " "}


@dataclass
class Char:
    """One rendered character with the chain of elements it sits in (innermost first).

    Parameters
    ----------
    char : str
        The character after whitespace handling.
    chain : tuple of Element
        The element holding the character followed by its ancestors up to the text.
    child : int
        Index of the character data within the innermost element's children.
    offset : int
        Index of the character within that string.
    local : dict of int to int
        For each element in the chain (keyed by ``id``), how many characters
        of that element precede this one.

    See Also
    --------
    collect : Produce the characters of a text.
    """

    char: str
    chain: tuple[Element, ...]
    child: int
    offset: int
    local: dict[int, int]


def _units(value: object, reference: float) -> float:
    length = Length.parse(value)
    if length.unit is Unit.PERCENT:
        return length.value * reference / PERCENT
    return length.to_user_units()


def number_list(value: object, reference: float = 0.0) -> list[float]:
    """Convert an SVG number or length list to floats.

    Accepts a string such as ``"1 2,3"``, a single number or a sequence of
    numbers and lengths.

    Parameters
    ----------
    value : object
        The list to convert; ``None`` gives an empty list.
    reference : float, optional
        Value that percentages resolve against. Defaults to 0.0.

    Returns
    -------
    list of float
        The values in user units.

    Examples
    --------
    >>> number_list("1 2,3")
    [1.0, 2.0, 3.0]
    >>> number_list("50%", 200)
    [100.0]
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [_units(v, reference) for v in value]
    if isinstance(value, (int, float)):
        return [float(value)]
    return [_units(v, reference) for v in str(value).replace(",", " ").split()]


def _raw(element: Element, chain: tuple[Element, ...], out: list[tuple[str, tuple[Element, ...], int, int]]) -> None:
    from .base import Element as _Element

    for position, child in enumerate(element.children):
        if isinstance(child, str):
            for offset, char in enumerate(child):
                out.append((char, chain, position, offset))
        elif isinstance(child, _Element) and child.tag in ("tspan", "a", "altGlyph"):
            _raw(child, (child, *chain), out)


def collect(text: Element) -> list[Char]:
    """Collect the rendered characters of a text.

    Applies ``xml:space`` handling: newlines are dropped, tabs become spaces
    and runs of spaces collapse, unless ``xml:space="preserve"``.

    Parameters
    ----------
    text : Element
        A ``<text>`` element.

    Returns
    -------
    list of Char
        One entry per rendered character, each with its element chain.

    Examples
    --------
    >>> import svgwriter as svg
    >>> "".join(c.char for c in collect(svg.text("a  b", x=0, y=0)))
    'a b'
    """
    raw: list[tuple[str, tuple[Element, ...], int, int]] = []
    _raw(text, (text,), raw)
    preserve = str(text.get("xml:space", "default")) == "preserve"
    kept: list[tuple[str, tuple[Element, ...], int, int]] = []
    for char, chain, child, offset in raw:
        mapped = char.translate(_PRESERVE if preserve else _DEFAULT)
        if not mapped:
            continue
        if not preserve and mapped == " " and (not kept or kept[-1][0] == " "):
            continue
        kept.append((mapped, chain, child, offset))
    if not preserve:
        while kept and kept[-1][0] == " ":
            kept.pop()
    counters: dict[int, int] = {}
    chars = []
    for char, chain, child, offset in kept:
        local = {}
        for element in chain:
            local[id(element)] = counters.get(id(element), 0)
            counters[id(element)] = local[id(element)] + 1
        chars.append(Char(char, chain, child, offset, local))
    return chars


def _font_weight(value: object) -> int:
    text = str(value).strip()
    return FONT_WEIGHTS.get(text, int(text) if text.isdigit() else FONT_WEIGHTS["normal"])


def _font_size(value: object) -> float:
    text = str(value).strip()
    if text in FONT_SIZE_KEYWORDS:
        return FONT_SIZE_KEYWORDS[text]
    try:
        size = Length.parse(value)
    except ValueError:
        return DEFAULT_FONT_SIZE
    return size.value * DEFAULT_FONT_SIZE / PERCENT if size.unit is Unit.PERCENT else size.to_user_units()


def _viewport(element: Element) -> tuple[float, float]:
    root = element.root()
    box = getattr(root, "view_box", None)
    return (box.width, box.height) if box else (0.0, 0.0)


class _Lists:
    """Per-element positioning lists, parsed once per layout."""

    def __init__(self, width: float, height: float) -> None:
        self.reference = {"x": width, "dx": width, "y": height, "dy": height, "rotate": 0.0}
        self.cache: dict[tuple[int, str], list[float]] = {}

    def of(self, element: Element, name: str) -> list[float]:
        key = (id(element), name)
        if key not in self.cache:
            self.cache[key] = number_list(element.get(name), self.reference[name])
        return self.cache[key]

    def value(self, char: Char, name: str) -> float | None:
        for element in char.chain:
            values = self.of(element, name)
            index = char.local[id(element)]
            if index < len(values):
                return values[index]
            if name == "rotate" and values:
                return values[-1]
        return None


def layout(text: Element, rules: list[Rule] | None = None) -> list[GlyphBox]:
    """Place every character of *text* (``tspan`` positions and fonts included).

    Parameters
    ----------
    text : Element
        A ``<text>`` element.
    rules : list of Rule, optional
        Pre-collected style sheet rules (collected from the root otherwise).

    Returns
    -------
    list of GlyphBox
        One box per rendered character; ``source`` is the innermost element.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(layout(svg.text("abc", x=0, y=20)))
    3
    """
    from ..ops.text import ANCHOR_SHIFT, GlyphBox, glyph_shape

    if rules is None:
        root = text.root()
        rules = rules_of(root) if root is not text else []
    chars = collect(text)
    lists = _Lists(*_viewport(text))
    fonts: dict[int, tuple[str, float, int, bool]] = {}
    boxes: list[GlyphBox] = []
    chunks: list[int] = [0]
    pen_x = pen_y = 0.0
    for index, char in enumerate(chars):
        source = char.chain[0]
        if id(source) not in fonts:
            fonts[id(source)] = (
                str(computed(source, "font-family", DEFAULT_FONT_FAMILY, rules)),
                _font_size(computed(source, "font-size", DEFAULT_FONT_SIZE, rules)),
                _font_weight(computed(source, "font-weight", "normal", rules)),
                str(computed(source, "font-style", "", rules)) in ("italic", "oblique"),
            )
        family, size, weight, italic = fonts[id(source)]
        x, y = lists.value(char, "x"), lists.value(char, "y")
        if x is not None:
            pen_x = x
            if index:
                chunks.append(index)
        if y is not None:
            pen_y = y
        pen_x += lists.value(char, "dx") or 0.0
        pen_y += lists.value(char, "dy") or 0.0
        outline, advance = glyph_shape(char.char, family, size, weight, italic)
        boxes.append(GlyphBox(char.char, outline, pen_x, pen_y, lists.value(char, "rotate") or 0.0, advance, source))
        pen_x += advance
    chunks.append(len(boxes))
    for start, stop in zip(chunks, chunks[1:], strict=False):
        if start == stop:
            continue
        anchor = str(computed(boxes[start].source, "text-anchor", "start", rules))
        shift = ANCHOR_SHIFT.get(anchor, 0.0) * (boxes[stop - 1].x + boxes[stop - 1].advance - boxes[start].x)
        for box in boxes[start:stop]:
            box.x -= shift
    return boxes
