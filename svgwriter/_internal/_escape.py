"""
XML escaping for text and attribute values.
"""

from __future__ import annotations

from ._constants import ATTRIBUTE_TABLE, TEXT_TABLE

__all__ = ["escape_attribute", "escape_text"]


def escape_text(text: str) -> str:
    """Escape character data."""
    return text.translate(TEXT_TABLE)


def escape_attribute(text: str) -> str:
    """Escape a value for use inside double quotes."""
    return text.translate(ATTRIBUTE_TABLE)
