"""
Style rules: parsing CSS sheets and collecting the rules a tree's ``<style>`` elements and theme carry.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._constants import AT_BLOCK_RE, COMMENT_RE, IMPORTANT, ROOT_RULES, RULE_RE
from ._selectors import specificity

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["Rule", "frozen_rules", "parse_css", "rules_of", "set_class_rules"]

_FROZEN: ContextVar[dict[int, list[Rule]] | None] = ContextVar("svgwriter_frozen_rules", default=None)


@dataclass(frozen=True)
class Rule:
    """One selector with its declarations.

    Parameters
    ----------
    selector : str
        A single CSS selector (no commas).
    specificity : tuple of int
        ``(ids, classes, types)`` counts used to rank competing rules.
    order : int
        Position in the style sheet; later rules win ties.
    declarations : tuple of tuple
        ``(name, value, important)`` triples.

    See Also
    --------
    parse_css : Produces rules from CSS text.

    Examples
    --------
    >>> from svgwriter.model.attributes.rules import parse_css
    >>> rule = parse_css(".a { fill: red }")[0]
    >>> rule.selector, rule.specificity, rule.declarations
    ('.a', (0, 1, 0), (('fill', 'red', False),))
    """

    selector: str
    specificity: tuple[int, int, int]
    order: int
    declarations: tuple[tuple[str, str, bool], ...]


def parse_css(text: str, start: int = 0) -> list[Rule]:
    """Parse a style sheet into rules; ``@`` blocks are skipped.

    A rule with several comma-separated selectors becomes one `Rule` per
    selector. Comments are removed and ``!important`` is recorded per declaration.

    Parameters
    ----------
    text : str
        CSS text.
    start : int, optional
        Order number given to the first rule, so rules from several sheets stay ordered. Defaults to 0.

    Returns
    -------
    list of Rule
        The parsed rules in source order.

    See Also
    --------
    rules_of : Collect the rules of every ``<style>`` element.

    Examples
    --------
    >>> from svgwriter.model.attributes.rules import parse_css
    >>> [r.selector for r in parse_css("rect, .a { fill: red } /* x */ #b{stroke:blue}")]
    ['rect', '.a', '#b']
    """
    text = AT_BLOCK_RE.sub("", COMMENT_RE.sub("", text))
    rules: list[Rule] = []
    for selectors, body in RULE_RE.findall(text):
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
                rules.append(Rule(selector, specificity(selector), start + len(rules), tuple(declarations)))
    return rules


@contextmanager
def frozen_rules() -> Generator[None, None, None]:
    """Collect each tree's style rules once for the block, for many lookups while no ``<style>`` changes.

    Joins an enclosing block, so nesting is free.

    Yields
    ------
    None

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.attributes.rules import frozen_rules, rules_of
    >>> doc = svg.parse('<svg xmlns="http://www.w3.org/2000/svg"><style>.a{fill:red}</style></svg>')
    >>> with frozen_rules():
    ...     rules_of(doc) is rules_of(doc)
    True
    """
    if _FROZEN.get() is not None:
        yield
        return
    token = _FROZEN.set({})
    try:
        yield
    finally:
        _FROZEN.reset(token)


def rules_of(root: Element) -> list[Rule]:
    """Collect the rules of every ``<style>`` element under an element.

    Rules a document attaches to its root by class name (its theme's role styles) come first, for the
    classes the tree uses, so measuring before output sees the same styles as the output.

    Parameters
    ----------
    root : Element
        The element to search, including itself.

    Returns
    -------
    list of Rule
        The rules in document order, numbered consecutively.

    See Also
    --------
    parse_css : Parse a single sheet.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.attributes.rules import rules_of
    >>> doc = svg.parse('<svg xmlns="http://www.w3.org/2000/svg"><style>.a{fill:red}</style></svg>')
    >>> [rule.selector for rule in rules_of(doc)]
    ['.a']
    """
    cache = _FROZEN.get()
    if cache is not None and id(root) in cache:
        return cache[id(root)]
    by_class: dict[str, list[Rule]] = root.__dict__.get(ROOT_RULES) or {}
    sheets: list[str] = []
    used: set[str] = set()
    for element in root.iter():
        if element.tag == "style":
            sheets.append("".join(c for c in element.children if isinstance(c, str)))
        if by_class:
            used.update(str(element.attributes.get("class", "")).split())
    rules = [rule for name in sorted(used & by_class.keys()) for rule in by_class[name]]
    for css in sheets:
        rules.extend(parse_css(css, start=len(rules)))
    if cache is not None:
        cache[id(root)] = rules
    return rules


def set_class_rules(root: Element, rules: dict[str, list[Rule]]) -> None:
    """Attach rules by class name to *root*; :func:`rules_of` puts them first for the classes in use.

    Parameters
    ----------
    root : Element
        The root of a tree.
    rules : dict of str to list of Rule
        The rules of each class name, such as a theme's role styles.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.attributes.cascade import computed
    >>> from svgwriter.model.attributes.rules import parse_css, set_class_rules
    >>> root = svg.Svg(svg.rect(0, 0, 1, 1, class_="a"))
    >>> set_class_rules(root, {"a": parse_css(".a { fill: red }")})
    >>> computed(root[0], "fill")
    'red'
    """
    object.__setattr__(root, ROOT_RULES, rules)
