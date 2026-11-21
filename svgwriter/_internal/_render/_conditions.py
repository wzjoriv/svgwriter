"""
Conditional processing for a render copy: ``<switch>`` and the ``requiredFeatures``, ``requiredExtensions``
and ``systemLanguage`` tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._constants import FEATURE_PREFIX, NON_CONTENT, RENDER_LANGUAGE

if TYPE_CHECKING:
    from ...model.elements.core import Element

__all__ = ["apply_conditions", "passes"]


def passes(element: Element, language: str = RENDER_LANGUAGE) -> bool:
    """Whether *element*'s conditional attributes all hold.

    ``requiredFeatures`` holds when it lists only SVG 1.1 feature strings,
    ``requiredExtensions`` holds only when absent, since no extension is supported, and
    ``systemLanguage`` holds when one of its languages is *language* or a dialect of it.

    Parameters
    ----------
    element : Element
        The element to test.
    language : str, optional
        The user's language. Defaults to ``"en"``.

    Returns
    -------
    bool
        True when the element is rendered.

    Examples
    --------
    >>> import svgwriter as svg
    >>> passes(svg.rect(0, 0, 1, 1, system_language="fr, en-US"))
    True
    >>> passes(svg.rect(0, 0, 1, 1, system_language="fr"))
    False
    """
    features = element.get("requiredFeatures")
    if features is not None and (not str(features).split() or not all(
            name.startswith(FEATURE_PREFIX) for name in str(features).split())):
        return False
    if element.get("requiredExtensions") is not None:
        return False
    languages = element.get("systemLanguage")
    if languages is None:
        return True
    wanted = language.lower()
    for tag in str(languages).split(","):
        tag = tag.strip().lower()
        if tag == wanted or tag.startswith(wanted + "-"):
            return True
    return False


def apply_conditions(root: Element) -> None:
    """Drop elements whose conditions fail and turn each ``<switch>`` into a ``<g>`` of its first passing child.

    Parameters
    ----------
    root : Element
        A render copy; it is changed in place.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document.from_string(
    ...     '<svg xmlns="http://www.w3.org/2000/svg"><switch><rect systemLanguage="fr"/><circle/><path/></switch></svg>')
    >>> copy = doc.root.clone()
    >>> apply_conditions(copy)
    >>> [(e.tag, [c.tag for c in e]) for e in copy]
    [('g', ['circle'])]
    """
    from ...model.elements import Group
    from .._tree import replace_in_parent

    for element in [e for e in root.iter() if e is not root]:
        if element.parent is not None and not passes(element):
            element.parent.remove(element)
    for switch in [e for e in root.iter() if e.tag == "switch"]:
        group = Group()
        group.attributes.update(switch.attributes)
        chosen = next((child for child in switch if not isinstance(child, str) and child.tag not in NON_CONTENT), None)
        if chosen is not None:
            switch.remove(chosen)
            group.add(chosen)
        replace_in_parent(switch, group)
