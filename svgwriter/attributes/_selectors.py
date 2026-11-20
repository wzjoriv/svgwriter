"""
CSS selector pieces: specificity and compound-selector matching.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ._constants import COMPOUND_RE

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["matches_compound", "specificity"]


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
