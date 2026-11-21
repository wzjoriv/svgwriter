"""
Named canvas sizes: paper, slides, video, social images and icons (``Document(size="a4")``).
"""

from __future__ import annotations

import difflib
from typing import Final

from .._internal._registry import Registry
from ..attributes.length import Length, LengthLike
from ._constants import BUILTIN_SIZES, LANDSCAPE_SUFFIX, PORTRAIT_SUFFIX

__all__ = ["SIZES", "page_size", "register_size", "unregister_size"]

SIZES: Final[Registry[tuple[Length, Length]]] = Registry("size")
"""Every named size as ``name -> (width, height)``: ``SIZES.names()`` lists them, ``page_size`` looks one up."""


def _length(value: LengthLike) -> Length:
    return value if isinstance(value, Length) else Length.parse(value) if isinstance(value, str) else Length(float(value))


def register_size(name: str, width: LengthLike, height: LengthLike) -> None:
    """Add a named canvas size for ``Document(size=name)``, ``Scene.size`` and project files.

    Sizes with a physical unit (``"210mm"``, ``svg.inch(11)``) make documents whose ``viewBox`` counts
    in that unit, so drawing coordinates are millimetres or inches; plain numbers are pixels. Every
    name also works with ``-landscape`` and ``-portrait`` appended.

    Parameters
    ----------
    name : str
        The name, such as ``"poster-50x70"``.
    width, height : Length, float or str
        The size: a :class:`~svgwriter.Length`, length text such as ``"50cm"``, or pixels.

    Raises
    ------
    ValueError
        If *name* is taken, or the two lengths have different units.

    See Also
    --------
    unregister_size : Remove it again.
    page_size : Look a size up.
    SIZES : Every registered size.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.register_size("poster-50x70", "50cm", "70cm")
    >>> svg.Document(size="poster-50x70-landscape").root.get("viewBox").width
    70.0
    >>> svg.unregister_size("poster-50x70")
    """
    first, second = _length(width), _length(height)
    if first.unit is not second.unit:
        raise ValueError(f"size {name!r}: width and height need one unit, not {first} and {second}")
    SIZES.add(name, (first, second))


def unregister_size(name: str) -> None:
    """Remove a size added with :func:`register_size`.

    Parameters
    ----------
    name : str
        The registered name.

    Raises
    ------
    KeyError
        If no size has that name.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.register_size("square", 100, 100)
    >>> svg.unregister_size("square")
    >>> "square" in svg.SIZES
    False
    """
    SIZES.remove(name)


def page_size(name: str) -> tuple[Length, Length]:
    """The width and height registered as *name*, turned for a ``-landscape`` or ``-portrait`` suffix.

    Parameters
    ----------
    name : str
        A name from :data:`SIZES` (``"a4"``, ``"letter"``, ``"slide-16:9"``, ``"instagram-story"``,
        ...), optionally followed by ``-landscape`` (long side across) or ``-portrait`` (long side down).

    Returns
    -------
    tuple of Length
        ``(width, height)``.

    Raises
    ------
    ValueError
        If the name is unknown; the message suggests the closest names.

    See Also
    --------
    register_size : Add a size.

    Examples
    --------
    >>> import svgwriter as svg
    >>> [str(side) for side in svg.page_size("a4-landscape")]
    ['297mm', '210mm']
    >>> svg.page_size("a44")
    Traceback (most recent call last):
    ...
    ValueError: unknown size 'a44'; did you mean 'a4'? (svg.SIZES.names() lists every size)
    """
    base, turn = name, None
    for suffix in (LANDSCAPE_SUFFIX, PORTRAIT_SUFFIX):
        if name not in SIZES and name.endswith(suffix):
            base, turn = name.removesuffix(suffix), suffix
    if base not in SIZES:
        close = difflib.get_close_matches(base, SIZES.names(), n=3)
        hint = f"; did you mean {' or '.join(map(repr, close))}?" if close else ""
        raise ValueError(f"unknown size {name!r}{hint} (svg.SIZES.names() lists every size)")
    width, height = SIZES.get(base)
    if turn is not None and (width.value > height.value) != (turn == LANDSCAPE_SUFFIX):
        width, height = height, width
    return width, height


for _name, (_width, _height) in BUILTIN_SIZES.items():
    register_size(_name, _width, _height)
