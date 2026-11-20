"""
Text layout across ``<text>`` and nested ``<tspan>`` runs, following SVG 1.1's text rules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..._internal._fonts import font_size, font_weight
from ...attributes.cascade import Rule, computed, rules_of
from ...attributes.length import Length, Unit
from ._constants import (
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    PERCENT,
    POSITION_NAMES,
    WHITESPACE_DEFAULT,
    WHITESPACE_PRESERVE,
)

if TYPE_CHECKING:
    from ...ops.text import GlyphBox
    from ..core import Element

__all__ = ["Char", "collect", "layout", "number_list"]


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

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.elements.text._textlayout import collect
    >>> first = collect(svg.text("ab", x=0, y=0))[0]
    >>> first.char, first.offset, first.chain[-1].tag
    ('a', 0, 'text')
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
    from ..core import Element as _Element

    for position, child in enumerate(element.children):
        if isinstance(child, str):
            for offset, char in enumerate(child):
                out.append((char, chain, position, offset))
        elif isinstance(child, _Element) and child.tag in ("tspan", "a", "altGlyph", "textPath"):
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
        mapped = char.translate(WHITESPACE_PRESERVE if preserve else WHITESPACE_DEFAULT)
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
    from ..._internal._constants import ANCHOR_SHIFT
    from ...ops.text import GlyphBox, glyph_shape

    if rules is None:
        root = text.root()
        rules = rules_of(root) if root is not text else []
    chars = collect(text)
    lists = _Lists(*_viewport(text))
    fonts: dict[int, tuple[Any, ...]] = {}
    boxes: list[GlyphBox] = []
    chunks: list[int] = [0]
    pen_x = pen_y = 0.0
    shaped = _shaped_runs(chars, lists, fonts, rules)
    for index, char in enumerate(chars):
        source = char.chain[0]
        family, size, weight, italic, language = _font_key(source, fonts, rules)
        x, y = lists.value(char, "x"), lists.value(char, "y")
        if x is not None:
            pen_x = x
            if index:
                chunks.append(index)
        if y is not None:
            pen_y = y
        pen_x += lists.value(char, "dx") or 0.0
        pen_y += lists.value(char, "dy") or 0.0
        outline, advance = shaped[index] if index in shaped else glyph_shape(
            char.char, family, size, weight, italic, language)
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
    _along_paths(chars, boxes)
    return boxes


def _font_key(source: Element, fonts: dict[int, tuple[Any, ...]], rules: list[Rule]) -> tuple[Any, ...]:
    if id(source) not in fonts:
        fonts[id(source)] = (
            str(computed(source, "font-family", DEFAULT_FONT_FAMILY, rules)),
            font_size(computed(source, "font-size", DEFAULT_FONT_SIZE, rules)),
            font_weight(computed(source, "font-weight", "normal", rules)),
            str(computed(source, "font-style", "", rules)) in ("italic", "oblique"),
            _language(source),
        )
    return fonts[id(source)]


def _language(element: Element) -> str | None:
    """The nearest ``xml:lang`` (or ``lang``) of *element* or its ancestors."""
    node: Element | None = element
    while node is not None:
        value = node.get("xml:lang") or node.get("lang")
        if value:
            return str(value)
        node = node.parent
    return None


def _shaped_runs(chars: list[Char], lists: Any, fonts: dict[int, tuple[Any, ...]],
                 rules: list[Rule]) -> dict[int, tuple[Any, float]]:
    """Shaped ``(outline, advance)`` by character index, for runs in one font that need a shaper."""
    from ..._internal._shaping import needs_shaping, shape_run

    result: dict[int, tuple[Any, float]] = {}
    start = 0
    while start < len(chars):
        key = _font_key(chars[start].chain[0], fonts, rules)
        stop = start + 1
        while stop < len(chars) and _font_key(chars[stop].chain[0], fonts, rules) == key and not any(
                lists.value(chars[stop], name) is not None for name in POSITION_NAMES):
            stop += 1
        for first, last in _font_segments(chars, start, stop, key):
            run = "".join(char.char for char in chars[first:last])
            if needs_shaping(run):
                for offset, item in enumerate(shape_run(run, *key)):
                    result[first + offset] = item
        start = stop
    return result


def _font_segments(chars: list[Char], start: int, stop: int, key: tuple[Any, ...]) -> list[tuple[int, int]]:
    """Split ``chars[start:stop]`` where the fallback font changes, so each piece is shaped in a font that has it.

    Spaces and combining marks stay with the character before them.
    """
    import unicodedata

    from ..._internal._fonts import font_for

    segments: list[tuple[int, int]] = []
    current, begin = None, start
    for index in range(start, stop):
        char = chars[index].char
        if char.isspace() or unicodedata.combining(char) or unicodedata.category(char) in ("Mn", "Mc", "Cf"):
            continue
        family = font_for(char, *key).getTypeface().getFamilyName()
        if current is not None and family != current:
            segments.append((begin, index))
            begin = index
        current = family
    segments.append((begin, stop))
    return segments


def _guide(holder: Element) -> Any:
    """The outline a ``<textPath>`` follows, in the text's user space, or None."""
    href = holder.get("xlink:href") or holder.get("href")
    target = getattr(href, "element", None)
    if target is None and href is not None:
        target = holder.root().get_element_by_id(str(href).lstrip("#"))
    outline = getattr(target, "outline", None)
    return outline() if outline is not None else None


def _start_offset(holder: Element, length: float) -> float:
    value = str(holder.get("startOffset", 0)).strip()
    return float(value[:-1]) / PERCENT * length if value.endswith("%") else float(value or 0)


def _along_paths(chars: list[Char], boxes: list[Any]) -> None:
    """Move the glyphs of each ``<textPath>`` onto its path: middles at their advance, turned with the tangent."""
    from ...ops.measure import point_at_length, tangent_at_length, total_length
    from ...pathdata.data import PathData

    runs: dict[int, tuple[Element, list[int]]] = {}
    for index, char in enumerate(chars):
        holder = next((element for element in char.chain if element.tag == "textPath"), None)
        if holder is not None:
            runs.setdefault(id(holder), (holder, []))[1].append(index)
    for holder, indices in runs.values():
        guide = _guide(holder)
        if guide is None or not len(guide):
            continue
        length = total_length(guide)
        offset = _start_offset(holder, length)
        origin, baseline = boxes[indices[0]].x, boxes[indices[0]].y
        for index in indices:
            box = boxes[index]
            middle = offset + box.x - origin + box.advance / 2
            if not 0 <= middle <= length:
                box.outline = PathData()
                continue
            point, tangent = point_at_length(guide, middle), tangent_at_length(guide, middle)
            angle = math.atan2(tangent.y, tangent.x)
            cos, sin, rise = math.cos(angle), math.sin(angle), box.y - baseline
            box.x = point.x - cos * box.advance / 2 - sin * rise
            box.y = point.y - sin * box.advance / 2 + cos * rise
            box.angle += math.degrees(angle)
