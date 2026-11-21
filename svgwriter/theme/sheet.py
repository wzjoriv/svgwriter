"""
The theme ``<style>`` sheet of a tree: the roles it uses and the sheet written while it is output.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from ._constants import ROLE_CLASS_PREFIX, SHEET_THEME_NAME, STYLE_ID
from ._errors import ThemeError
from .theme import THEMES, Theme

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["STYLE_ID", "applied", "sheet_theme", "used_roles"]


def used_roles(theme: Theme, root: Element) -> list[str]:
    """The roles of *theme* that elements under *root* carry, in theme order.

    Parameters
    ----------
    theme : Theme
        The theme whose roles are looked for.
    root : Element
        The tree to search, including itself.

    Returns
    -------
    list of str
        Role names.

    Raises
    ------
    ThemeError
        If an element carries a ``role-`` class that the theme does not define.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.theme.sheet import used_roles
    >>> g = svg.group(svg.circle(0, 0, 1).as_role("dot"), svg.rect(0, 0, 1, 1).as_role("box"))
    >>> used_roles(svg.Theme.get("light"), g)
    ['box', 'dot']
    """
    by_class = {Theme.class_name(role): role for role in theme.roles}
    found: set[str] = set()
    for element in root.iter():
        for name in str(element.attributes.get("class", "")).split():
            if not name.startswith(ROLE_CLASS_PREFIX):
                continue
            if name not in by_class:
                raise ThemeError(f"<{element.tag}> has class {name!r} but theme {theme.name!r} has no such role")
            found.add(by_class[name])
    return [role for role in theme.roles if role in found]


@contextmanager
def applied(theme: Theme, root: Element) -> Generator[None, None, None]:
    """Hold the theme sheet in *root* for the duration of the block.

    The sheet is a ``<style id="svgwriter-theme">`` with rules for the roles in use. An existing one
    (from a parsed file) has its text replaced; otherwise one is inserted at the top. The tree is
    restored on exit. Nothing is written when no role is used and no sheet exists.

    Parameters
    ----------
    theme : Theme
        The theme to apply.
    root : Element
        The root ``<svg>``.

    Yields
    ------
    None

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.theme.sheet import applied
    >>> root = svg.Svg(svg.circle(0, 0, 1).as_role("dot"))
    >>> with applied(svg.Theme.get("mono"), root):
    ...     root[0].css
    '.role-dot { fill:#000000;stroke:#000000;stroke-width:1px }'
    >>> len(root)
    1
    """
    from ..elements.structure import StyleElement, Title

    roles = used_roles(theme, root)
    existing = root.get_element_by_id(STYLE_ID)
    if not roles and existing is None:
        yield
        return
    css = theme.css(roles).css()
    if isinstance(existing, StyleElement):
        saved = existing.css
        existing.css = css
        try:
            yield
        finally:
            existing.css = saved
        return
    first = next(iter(root.children), None)
    sheet = root.insert(1 if isinstance(first, Title) else 0, StyleElement(css, id=STYLE_ID))
    try:
        yield
    finally:
        root.remove(sheet)


def sheet_theme(root: Element) -> Theme | None:
    """The theme that wrote the theme sheet of a parsed tree, so reopening a file keeps its look.

    A registered theme that writes exactly that sheet is returned; otherwise the current theme
    with the sheet's role styles, named ``"document"``.

    Parameters
    ----------
    root : Element
        The root ``<svg>``.

    Returns
    -------
    Theme or None
        The theme, or None when the tree has no theme sheet.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.theme.sheet import sheet_theme
    >>> doc = svg.Document(10, 10, theme="dark")
    >>> _ = doc.circle(5, 5, 2).as_role("dot")
    >>> sheet_theme(svg.parse(doc.to_string())).name
    'dark'
    >>> sheet_theme(svg.Svg()) is None
    True
    """
    from ..attributes.cascade import parse_css
    from ..elements.structure import StyleElement

    sheet = root.get_element_by_id(STYLE_ID)
    if not isinstance(sheet, StyleElement):
        return None
    css = sheet.css
    for name in THEMES.names():
        theme = THEMES.get(name)
        try:
            roles = used_roles(theme, root)
        except ThemeError:
            continue
        if theme.css(roles).css() == css:
            return theme
    prefix = "." + ROLE_CLASS_PREFIX
    roles = {rule.selector.removeprefix(prefix).replace("-", "."): {key: value for key, value, _ in rule.declarations}
             for rule in parse_css(css) if rule.selector.startswith(prefix)}
    return Theme.current().replace(name=SHEET_THEME_NAME, roles=roles)
