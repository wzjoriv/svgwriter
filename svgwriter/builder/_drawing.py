"""
The ``drawing`` decorator: a function drawing into a fresh document.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, Concatenate

from .._internal._typing import P
from ..document import Document

__all__ = ["drawing"]


def drawing(width: float, height: float, **root: Any) -> Callable[[Callable[Concatenate[Document, P], object]], Callable[P, Document]]:
    """Turn ``f(doc, *args)`` into ``f(*args) -> Document``.

    The decorated function receives a fresh :class:`~svgwriter.Document` of the
    given size on every call and draws into it; its return value is ignored.

    Parameters
    ----------
    width, height : float
        Size of the document created for each call.
    **root
        Attributes forwarded to the :class:`~svgwriter.Document` constructor.

    Returns
    -------
    callable
        A decorator producing a function that returns the finished document.

    Examples
    --------
    >>> from svgwriter import Path
    >>> @drawing(10, 10)
    ... def dot(doc, color="red"):
    ...     doc.add(Path("M5 5 h1", stroke=color))
    >>> isinstance(dot(), Document)
    True
    """

    def decorate(func: Callable[Concatenate[Document, P], object]) -> Callable[P, Document]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Document:
            doc = Document(width, height, **root)
            func(doc, *args, **kwargs)
            return doc

        return wrapper

    return decorate
