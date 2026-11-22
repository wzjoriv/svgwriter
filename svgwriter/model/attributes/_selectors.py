"""
CSS selector pieces: specificity, compiling selectors once, compound matching and combinators.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, NamedTuple

from ._constants import (
    ANY_TAG,
    CLASS_KEY,
    COMBINATORS,
    COMPOUND_RE,
    DESCENDANT,
    FIRST_CHILD,
    ID_KEY,
    SELECTOR_CACHE_SIZE,
    TAG_KEY,
    UNIVERSAL_KEY,
)

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["Compound", "Selector", "compile_selector", "matches_selector", "specificity", "split_selector"]


class Compound(NamedTuple):
    """One compound selector, parsed: every test an element must pass."""

    tag: str | None
    ident: str | None
    classes: tuple[str, ...]
    attributes: tuple[tuple[str, str | None, str | None], ...]
    first_child: bool


class Selector(NamedTuple):
    """A compiled selector: compounds left to right and the combinator before each one but the first."""

    compounds: tuple[Compound, ...]
    combinators: tuple[str, ...]
    key: tuple[str, str]
    local: bool


def specificity(selector: str) -> tuple[int, int, int]:
    """CSS specificity ``(ids, classes, types)`` of a selector."""
    ids = len(re.findall(r"#[\w-]+", selector))
    classes = len(re.findall(r"\.[\w-]+|\[[^\]]*\]|:[\w-]+", selector))
    types = len(re.findall(r"(?:^|[\s>+~])([A-Za-z][\w-]*)", selector))
    return (ids, classes, types)


def split_selector(selector: str) -> list[str]:
    """Compound selectors and the combinators (``>``, ``+``, ``~``) between them; attribute brackets stay whole."""
    spaced, depth = [], 0
    for char in selector:
        depth += (char == "[") - (char == "]")
        spaced.append(f" {char} " if depth == 0 and char in COMBINATORS else char)
    return "".join(spaced).split()


def _compound(text: str) -> Compound | None:
    tag = ident = None
    classes: list[str] = []
    attributes: list[tuple[str, str | None, str | None]] = []
    first_child, position = False, 0
    for match in COMPOUND_RE.finditer(text):
        if match.start() != position:
            return None
        position = match.end()
        name, hash_, cls, attr, op, value, pseudo = match.groups()
        if name is not None and name != ANY_TAG:
            if tag is not None and tag != name:
                return None
            tag = name
        if hash_ is not None:
            if ident is not None and ident != hash_:
                return None
            ident = hash_
        if cls is not None:
            classes.append(cls)
        if attr is not None:
            attributes.append((attr, op, value))
        if pseudo is not None:
            if pseudo != FIRST_CHILD:
                return None
            first_child = True
    if position != len(text):
        return None
    return Compound(tag, ident, tuple(classes), tuple(attributes), first_child)


@lru_cache(maxsize=SELECTOR_CACHE_SIZE)
def compile_selector(selector: str) -> Selector | None:
    """Parse a selector once; ``None`` when it can never match (unsupported or malformed)."""
    parts = split_selector(selector)
    compounds: list[Compound] = []
    combinators: list[str] = []
    expect_compound = True
    for part in parts:
        if part in COMBINATORS:
            if expect_compound:
                return None
            combinators.append(part)
            expect_compound = True
            continue
        if not expect_compound:
            combinators.append(DESCENDANT)
        compound = _compound(part)
        if compound is None:
            return None
        compounds.append(compound)
        expect_compound = False
    if not compounds or expect_compound:
        return None
    last = compounds[-1]
    key = ((ID_KEY, last.ident) if last.ident is not None else (CLASS_KEY, last.classes[0]) if last.classes
           else (TAG_KEY, last.tag) if last.tag is not None else (UNIVERSAL_KEY, ""))
    return Selector(tuple(compounds), tuple(combinators), key, len(compounds) == 1 and not last.first_child)


def _matches_compound(element: Element, compound: Compound) -> bool:
    if compound.tag is not None and element.tag != compound.tag:
        return False
    attributes = element.attributes
    if compound.ident is not None and element.id != compound.ident:
        return False
    if compound.classes:
        classes = str(attributes.get("class", "")).split()
        if any(cls not in classes for cls in compound.classes):
            return False
    for name, op, value in compound.attributes:
        present = attributes.get(name)
        if present is None:
            return False
        text = str(present)
        if op == "=" and text != value:
            return False
        if op == "~=" and value not in text.split():
            return False
        if op == "|=" and not (text == value or text.startswith(f"{value}-")):
            return False
    if compound.first_child:
        parent = element.parent
        return parent is not None and next(iter(parent), None) is element
    return True


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


def _matches_from(element: Element, selector: Selector, index: int) -> bool:
    if not _matches_compound(element, selector.compounds[index]):
        return False
    if index == 0:
        return True
    combinator = selector.combinators[index - 1]
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
    return any(_matches_from(candidate, selector, index - 1) for candidate in candidates)


def matches_selector(element: Element, selector: Selector | None) -> bool:
    """Whether *element* matches a compiled selector (with backtracking over combinators)."""
    return selector is not None and _matches_from(element, selector, len(selector.compounds) - 1)
