"""
``ThemeError``: the one error of theme resolution, expressions and theme files.
"""

from __future__ import annotations

__all__ = ["ThemeError"]


class ThemeError(ValueError):
    """A theme that cannot be resolved: an unknown role or reference, a cycle, or a malformed value.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.theme.Palette({"a": "{palette.b}"})
    ... except svg.theme.ThemeError as error:
    ...     print(error)
    palette.a: unknown reference {palette.b}
    """
