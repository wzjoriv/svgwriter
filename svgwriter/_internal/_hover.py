"""
The ``<style>`` of ``:hover`` rules that ``element.on_hover(...)`` asks for, held while a document is written.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from ._constants import HOVER_SHEET_ID, HOVER_STYLE

if TYPE_CHECKING:
    from ..model.elements.core import Element

__all__ = ["hover_sheet"]


@contextmanager
def hover_sheet(root: Element) -> Generator[None, None, None]:
    """Insert ``#id:hover`` rules for every element under *root* with a hover style; removed on exit."""
    from ..model.elements.structure import StyleElement, Title

    rules = []
    for element in root.iter():
        style = element.__dict__.get(HOVER_STYLE)
        if style and element.id:
            body = ";".join(f"{name}:{value} !important" for name, value in style.items())
            rules.append(f"#{element.id}:hover {{ {body} }}")
    if not rules:
        yield
        return
    first = next(iter(root.children), None)
    sheet = root.insert(1 if isinstance(first, Title) else 0, StyleElement(" ".join(rules), id=HOVER_SHEET_ID))
    try:
        yield
    finally:
        root.remove(sheet)
