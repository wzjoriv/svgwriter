"""
``Keyword``: the base of svgwriter's enums of SVG keywords.
"""

from __future__ import annotations

import enum

__all__ = ["Keyword"]


class Keyword(str, enum.Enum):
    """A string enum whose ``str`` and ``format`` give the SVG keyword itself.

    Examples
    --------
    >>> from svgwriter._internal._enums import Keyword
    >>> class Side(Keyword):
    ...     LEFT = "left"
    >>> str(Side.LEFT), f"{Side.LEFT}", Side.LEFT == "left"
    ('left', 'left', True)
    """

    def __str__(self) -> str:
        return str(self.value)

    def __format__(self, spec: str) -> str:
        return format(str(self.value), spec)
