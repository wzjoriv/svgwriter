"""
``svg.preset.size``: a named canvas size.
"""

from __future__ import annotations

from ..._document.sizes import PageSize
from ..._internal._presets import SIZES
from ...model.attributes.length import LengthLike

__all__ = ["size"]


def size(name: str, width: LengthLike, height: LengthLike, *, replace: bool = False) -> PageSize:
    """Register a named canvas size for ``Document(size=name)``, ``Scene.size`` and project files.

    Sizes with a physical unit (``"210mm"``, ``svg.inch(11)``) make documents whose ``viewBox`` counts
    in that unit, so drawing coordinates are millimetres or inches; plain numbers are pixels. Every
    name also works with ``-landscape`` and ``-portrait`` appended, and appears as an attribute of
    :data:`svgwriter.size` with the name turned into an identifier.

    Parameters
    ----------
    name : str
        The name, such as ``"poster-50x70"``.
    width, height : Length, float or str
        The size: a :class:`~svgwriter.Length`, length text such as ``"50cm"``, or pixels.
    replace : bool, optional
        Replace a size already registered under the name, a built-in one included. Defaults to False.

    Returns
    -------
    PageSize
        The registered size.

    Raises
    ------
    ValueError
        If `name` is taken and `replace` is False, or the two lengths have different units.

    See Also
    --------
    svgwriter.catalog.preset.get : Look a size up by name (``get("size", name)``).
    svgwriter.catalog.preset.list : Every size (``list("size")``).
    svgwriter.catalog.preset.unregister : Remove it again (``unregister("size", name)``).

    Examples
    --------
    >>> import svgwriter as svg
    >>> _ = svg.preset.size("poster-50x70", "50cm", "70cm")
    >>> svg.size.poster_50x70.landscape.width
    70.0
    >>> svg.Document(size="poster-50x70-landscape").root.get("viewBox").width
    70.0
    >>> svg.preset.unregister("size", "poster-50x70")
    """
    return SIZES.add(name, PageSize.of(width, height), replace=replace)  # type: ignore[return-value]
