"""
CSS selector pieces: specificity, compound-selector matching and combinators.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ._constants import COMBINATORS, COMPOUND_RE

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["matches_compound", "matches_from", "specificity", "split_selector"]


def specificity(selector: str) -> tuple[int, int, int]:
    """CSS specificity ``(ids, classes, types)`` of a selector."""
    ids = len(re.findall(r"#[\w-]+", selector))
    classes = len(re.findall(r"\.[\w-]+|\[[^\]]*\]|:[\w-]+", selector))
    types = len(re.findall(r"(?:^|[\s>+~])([A-Za-z][\w-]*)", selector))
    return (ids, classes, types)



def matches_compound(element: Element, compound: str) -> bool:
    """Whether *element* matches one compound selector (no combinators)."""
    position = 0
    for match in COMPOUND_RE.finditer(compound):
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


def split_selector(selector: str) -> list[str]:
    """Compound selectors and the combinators (``>``, ``+``, ``~``) between them; attribute brackets stay whole."""
    spaced, depth = [], 0
    for char in selector:
        depth += (char == "[") - (char == "]")
        spaced.append(f" {char} " if depth == 0 and char in COMBINATORS else char)
    return "".join(spaced).split()


def _siblings_before(element: Element) -> list[Element]:
    from ..elements.core import Element as _Element

    parent = element.parent
    if parent is None:
        return []
    before = []
    for child in parent:
        if child is element:
            break
        if isinstance(child, _Element):
            before.append(child)
    return before[::-1]


def matches_from(element: Element, parts: list[str], index: int) -> bool:
    """Whether *element* matches ``parts[index]`` and everything left of it (with backtracking)."""
    if not matches_compound(element, parts[index]):
        return False
    if index == 0:
        return True
    combinator, rest = (parts[index - 1], index - 2) if parts[index - 1] in COMBINATORS else (" ", index - 1)
    if rest < 0:
        return False
    if combinator == ">":
        candidates = [element.parent] if element.parent is not None else []
    elif combinator == "+":
        candidates = _siblings_before(element)[:1]
    elif combinator == "~":
        candidates = _siblings_before(element)
    else:
        candidates, node = [], element.parent
        while node is not None:
            candidates.append(node)
            node = node.parent
    return any(matches_from(candidate, parts, rest) for candidate in candidates)
