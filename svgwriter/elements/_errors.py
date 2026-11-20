"""
Errors for unknown attributes and keywords, with lazy "did you mean" suggestions.
"""

from __future__ import annotations

import difflib
from typing import Final

from ..attributes.names import KNOWN_ATTRIBUTES, py_name

SUGGESTIONS: Final = 3
_PY_NAMES: Final = sorted({py_name(n) for n in KNOWN_ATTRIBUTES})

class UnknownAttributeError(AttributeError):
    """An attribute that is neither a Python member nor a known SVG attribute.

    The "did you mean" suggestion is computed only when the message is shown,
    so ``getattr(element, name, default)`` stays cheap.

    Parameters
    ----------
    owner : str
        The class name of the element.
    name : str
        The attribute that was requested.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.rect(0, 0, 1, 1).widht
    ... except AttributeError as error:
    ...     print("did you mean 'width'?" in str(error))
    True
    """

    def __init__(self, owner: str, name: str, members: type | None = None) -> None:
        super().__init__(name)
        self.owner = owner
        self.attribute = name
        self.members = members

    def __str__(self) -> str:
        methods = [m for m in dir(self.members) if not m.startswith("_")] if self.members is not None else []
        hint = [m for m in methods if m.startswith(self.attribute)][:SUGGESTIONS] or difflib.get_close_matches(
            self.attribute, [*methods, *_PY_NAMES], n=1)
        suggestion = f"; did you mean {' or '.join(map(repr, hint))}?" if hint else ""
        return (f"{self.owner} has no attribute {self.attribute!r}{suggestion} "
                "(unlisted SVG attributes: element.set(name, value))")


class UnknownKeywordError(UnknownAttributeError, TypeError):
    """An unknown keyword argument (likely a typo); custom attributes go in ``attrs={...}``.

    Parameters
    ----------
    owner : str
        The class name of the element.
    name : str
        The keyword that was given.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.rect(0, 0, 1, 1, widht=3)
    ... except TypeError as error:
    ...     print(type(error).__name__)
    UnknownKeywordError
    """

    def __str__(self) -> str:
        hint = difflib.get_close_matches(self.attribute, _PY_NAMES, n=1)
        suggestion = f"; did you mean {hint[0]!r}?" if hint else ""
        return (f"{self.owner}() got an unknown attribute keyword {self.attribute!r}{suggestion} "
                "(custom attributes: attrs={...} or data_* keywords)")
