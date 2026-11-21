"""
CSS style sheets and computed values: parsing, selector matching and inheritance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ._constants import (
    CSS_DIMENSION_RE,
    MARKER_LONGHANDS,
    ROOT_RULES,
)
from ._selectors import matches_from, split_selector
from .names import PRESENTATION_ATTRIBUTES
from .rules import Rule, rules_of

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["INHERITED", "computed", "css_declarations", "matches", "resolve_styles", "specified"]


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


def matches(element: Element, selector: str) -> bool:
    """Return whether an element matches a CSS selector.

    Supports type, ``*``, ``#id``, ``.class``, attribute selectors, ``:first-child``
    and the descendant, child (``>``), adjacent (``+``) and general (``~``) sibling combinators.

    Parameters
    ----------
    element : Element
        The element to test.
    selector : str
        A single selector, without commas.

    Returns
    -------
    bool
        True if the element matches.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.attributes.cascade import matches
    >>> g = svg.Group(class_="icon")
    >>> rect = g.append(svg.Rect(width=1, height=1))
    >>> matches(rect, "g.icon > rect")
    True
    >>> matches(rect, ".other rect")
    False
    """
    parts = split_selector(selector)
    return bool(parts) and matches_from(element, parts, len(parts) - 1)


def css_declarations(element: Element, rules: list[Rule]) -> dict[str, str]:
    """Return the declarations from style rules that apply to an element.

    Conflicts are resolved by ``!important``, then specificity, then source order.

    Parameters
    ----------
    element : Element
        The element to style.
    rules : list of Rule
        Candidate rules, as from `rules_of`.

    Returns
    -------
    dict of str to str
        The winning value for each property.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.attributes.cascade import css_declarations
    >>> from svgwriter.model.attributes.rules import parse_css
    >>> rect = svg.Rect(0, 0, 1, 1, class_="a", id="r")
    >>> rules = parse_css(".a { fill: red } #r { fill: blue }")
    >>> css_declarations(rect, rules)
    {'fill': 'blue'}
    """
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
    """Return the value set directly on an element.

    Looks at the inline ``style`` first, then matching style rules, then the
    presentation attribute. Nothing is inherited.

    Parameters
    ----------
    element : Element
        The element to inspect.
    name : str
        CSS property name, such as ``"fill"``.
    rules : list of Rule, optional
        Style rules to consult; collected from the element's document when omitted. Defaults to None.

    Returns
    -------
    object or None
        The specified value, or ``None`` when the element does not set it.

    See Also
    --------
    computed : The value after inheritance.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.attributes.cascade import specified
    >>> specified(svg.Rect(0, 0, 1, 1, fill="red", style="opacity:.5"), "opacity")
    '.5'
    >>> specified(svg.Rect(0, 0, 1, 1), "fill") is None
    True
    """
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
    """Return the computed value of a property.

    The value is the one specified on the element, else inherited from the
    nearest ancestor if the property inherits, else the default. The keyword
    ``inherit`` defers to the parent for any property.

    Parameters
    ----------
    element : Element
        The element to inspect.
    name : str
        CSS property name, such as ``"fill"``.
    default : object, optional
        Returned when no value applies. Defaults to None.
    rules : list of Rule, optional
        Style rules to consult; collected from the element's document when omitted. Defaults to None.

    Returns
    -------
    object
        The computed value.

    See Also
    --------
    specified : The value set on the element itself.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.attributes.cascade import computed
    >>> g = svg.Group(fill="green", opacity=0.5)
    >>> rect = g.append(svg.Rect(width=1, height=1))
    >>> computed(rect, "fill")
    'green'
    >>> computed(rect, "opacity", "1")
    '1'
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
    """Rewrite a tree so CSS and inline styles become presentation attributes.

    The tree is modified in place: matching rule declarations and inline
    ``style`` values are written as attributes and the ``style`` attribute is
    removed; ``<style>`` sheets, now folded in, are removed too, so later lookups do not apply
    their rules a second time over inline values. Renderers that ignore CSS then see the same result. The CSS-only ``marker``
    shorthand becomes ``marker-start``, ``marker-mid`` and ``marker-end``, and CSS units, which
    are case-insensitive (``20PX``), are written in the lower case attributes require.

    Parameters
    ----------
    root : Element
        The root of the tree to rewrite.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.attributes.cascade import resolve_styles
    >>> doc = svg.parse('<svg xmlns="http://www.w3.org/2000/svg"><rect style="fill:red"/></svg>')
    >>> resolve_styles(doc)
    >>> next(doc.iter("rect")).attributes["fill"]
    'red'
    """
    rules = rules_of(root)
    for element in root.iter():
        values = css_declarations(element, rules) if rules else {}
        values.update(_inline(element))
        if "marker" in values:
            shorthand = values.pop("marker")
            values = {**dict.fromkeys(MARKER_LONGHANDS, shorthand), **values}
        if not values:
            continue
        element.attributes.pop("style", None)
        for name, value in values.items():
            if name in PRESENTATION_ATTRIBUTES or name in ("transform",):
                dimension = CSS_DIMENSION_RE.match(str(value))
                element.attributes[name] = (dimension[1] + dimension[2].lower()) if dimension else value
    for sheet in list(root.iter("style")):
        if sheet.parent is not None:
            sheet.parent.remove(sheet)
    root.__dict__.pop(ROOT_RULES, None)

