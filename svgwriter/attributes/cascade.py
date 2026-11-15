"""CSS style sheets and computed values: parsing, selector matching and inheritance."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from .names import PRESENTATION_ATTRIBUTES

if TYPE_CHECKING:
    from ..elements.base import Element

__all__ = ["INHERITED", "Rule", "computed", "parse_css", "resolve_styles", "rules_of"]

INHERITED: Final = frozenset({
    "clip-rule", "color", "color-interpolation", "color-interpolation-filters", "color-profile", "color-rendering",
    "cursor", "direction", "fill", "fill-opacity", "fill-rule", "font", "font-family", "font-size",
    "font-size-adjust", "font-stretch", "font-style", "font-variant", "font-weight", "glyph-orientation-horizontal",
    "glyph-orientation-vertical", "image-rendering", "kerning", "letter-spacing", "marker", "marker-end",
    "marker-mid", "marker-start", "pointer-events", "shape-rendering", "stroke", "stroke-dasharray",
    "stroke-dashoffset", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-opacity",
    "stroke-width", "text-anchor", "text-rendering", "visibility", "word-spacing", "writing-mode",
})
"""Properties that inherit by default (SVG 1.1, appendix N)."""

_COMMENT_RE: Final = re.compile(r"/\*.*?\*/", re.S)
_RULE_RE: Final = re.compile(r"([^{}@]+)\{([^}]*)\}")
_AT_BLOCK_RE: Final = re.compile(r"@[^{;]+(\{(?:[^{}]|\{[^{}]*\})*\}|;)")
_COMPOUND_RE: Final = re.compile(r"(\*|[A-Za-z][\w-]*)|#([\w-]+)|\.([\w-]+)|\[([\w:-]+)(?:([~|]?=)\"?([^\"\]]*)\"?)?\]|(:[\w-]+(?:\([^)]*\))?)")
IMPORTANT: Final = "!important"


@dataclass(frozen=True)
class Rule:
    """One selector with its declarations."""

    selector: str
    specificity: tuple[int, int, int]
    order: int
    declarations: tuple[tuple[str, str, bool], ...]


def _specificity(selector: str) -> tuple[int, int, int]:
    ids = len(re.findall(r"#[\w-]+", selector))
    classes = len(re.findall(r"\.[\w-]+|\[[^\]]*\]|:[\w-]+", selector))
    types = len(re.findall(r"(?:^|[\s>+~])([A-Za-z][\w-]*)", selector))
    return (ids, classes, types)


def parse_css(text: str, start: int = 0) -> list[Rule]:
    """Parse a style sheet into rules; ``@`` blocks are skipped.

    Examples
    --------
    >>> [r.selector for r in parse_css("rect, .a { fill: red } /* x */ #b{stroke:blue}")]
    ['rect', '.a', '#b']
    """
    text = _AT_BLOCK_RE.sub("", _COMMENT_RE.sub("", text))
    rules: list[Rule] = []
    for selectors, body in _RULE_RE.findall(text):
        declarations = []
        for item in body.split(";"):
            name, sep, value = item.partition(":")
            if not sep or not name.strip():
                continue
            value = value.strip()
            important = value.lower().endswith(IMPORTANT)
            if important:
                value = value[: -len(IMPORTANT)].strip()
            declarations.append((name.strip().lower(), value, important))
        for selector in selectors.split(","):
            selector = " ".join(selector.split())
            if selector:
                rules.append(Rule(selector, _specificity(selector), start + len(rules), tuple(declarations)))
    return rules


def _matches_compound(element: Element, compound: str) -> bool:
    position = 0
    for match in _COMPOUND_RE.finditer(compound):
        if match.start() != position:
            return False
        position = match.end()
        tag, ident, cls, attr, op, value, pseudo = match.groups()
        if tag is not None and tag != "*" and element.tag != tag:
            return False
        if ident is not None and element.id != ident:
            return False
        if cls is not None and cls not in str(element.attributes.get("class", "")).split():
            return False
        if attr is not None:
            present = element.attributes.get(attr)
            if present is None:
                return False
            if op == "=" and str(present) != value:
                return False
            if op == "~=" and value not in str(present).split():
                return False
            if op == "|=" and not (str(present) == value or str(present).startswith(value + "-")):
                return False
        if pseudo is not None and not _pseudo(element, pseudo):
            return False
    return position == len(compound)


def _pseudo(element: Element, pseudo: str) -> bool:
    if pseudo == ":first-child":
        parent = element.parent
        return parent is not None and next(iter(parent), None) is element
    return False


def matches(element: Element, selector: str) -> bool:
    """Whether *element* matches a CSS *selector* (descendant and child combinators supported)."""
    parts = selector.replace(">", " > ").split()
    if not parts or not _matches_compound(element, parts[-1]):
        return False
    node: Element | None = element
    index = len(parts) - 2
    while index >= 0:
        combinator = " "
        if parts[index] == ">":
            combinator, index = ">", index - 1
        if index < 0:
            return False
        compound = parts[index]
        node = node.parent if node is not None else None
        if combinator == ">":
            if node is None or not _matches_compound(node, compound):
                return False
        else:
            while node is not None and not _matches_compound(node, compound):
                node = node.parent
            if node is None:
                return False
        index -= 1
    return True


def rules_of(root: Element) -> list[Rule]:
    """All rules from the ``<style>`` elements under *root*, in document order."""
    rules: list[Rule] = []
    for style in root.iter("style"):
        css = "".join(c for c in style.children if isinstance(c, str))
        rules.extend(parse_css(css, start=len(rules)))
    return rules


def css_declarations(element: Element, rules: list[Rule]) -> dict[str, str]:
    """Declarations from *rules* that apply to *element*, after specificity and ``!important``."""
    winners: dict[str, tuple[tuple[bool, tuple[int, int, int], int], str]] = {}
    for rule in rules:
        if not matches(element, rule.selector):
            continue
        for name, value, important in rule.declarations:
            rank = (important, rule.specificity, rule.order)
            if name not in winners or rank >= winners[name][0]:
                winners[name] = (rank, value)
    return {name: value for name, (_, value) in winners.items()}


def _inline(element: Element) -> dict[str, str]:
    raw = element.attributes.get("style")
    if raw is None:
        return {}
    if hasattr(raw, "items"):
        return {str(k): str(v) for k, v in raw.items()}
    return {k.strip().lower(): v.strip() for k, sep, v in
            (item.partition(":") for item in str(raw).split(";")) if sep}


def specified(element: Element, name: str, rules: list[Rule] | None = None) -> object | None:
    """The value set on *element* itself: inline style, then CSS, then the presentation attribute."""
    inline = _inline(element)
    if name in inline:
        return inline[name]
    if rules is None:
        rules = rules_of(element.root())
    sheet = css_declarations(element, rules) if rules else {}
    if name in sheet:
        return sheet[name]
    return element.attributes.get(name)


def computed(element: Element, name: str, default: object = None, rules: list[Rule] | None = None) -> object:
    """The computed value of property *name*: specified here, else inherited (if it inherits), else *default*.

    ``inherit`` defers to the parent for any property.
    """
    if rules is None:
        rules = rules_of(element.root())
    node: Element | None = element
    while node is not None:
        value = specified(node, name, rules)
        if value is not None and str(value).strip() != "inherit":
            return value
        if value is None and name not in INHERITED:
            return default
        node = node.parent
    return default


def resolve_styles(root: Element) -> None:
    """Rewrite *root*'s tree so CSS and inline styles become presentation attributes (in place)."""
    rules = rules_of(root)
    for element in root.iter():
        values = css_declarations(element, rules) if rules else {}
        values.update(_inline(element))
        if not values:
            continue
        element.attributes.pop("style", None)
        for name, value in values.items():
            if name in PRESENTATION_ATTRIBUTES or name in ("transform",):
                element.attributes[name] = value
