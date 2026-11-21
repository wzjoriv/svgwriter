"""
The theme ``<style>`` sheet of a tree: the roles it uses and the sheet written while it is output.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from ._constants import ROLE_CLASS_PREFIX, STYLE_ID
from ._errors import ThemeError
from .theme import Theme

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["STYLE_ID", "applied", "used_roles"]


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
