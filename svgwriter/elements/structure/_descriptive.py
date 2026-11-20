"""
``desc``, ``title`` and ``metadata``.
"""

from __future__ import annotations

from typing import Any

from .._behavior._mixins import CoreAttributes, StyleAttributes
from ..core._element import Category, Child, ContentModel

__all__ = ["Desc", "Metadata", "Title"]


class _Descriptive(StyleAttributes, CoreAttributes, category=Category.DESCRIPTIVE, content=ContentModel.TEXT):
    def __init__(self, text: str = "", **kwargs: Any) -> None:
        super().__init__(*([text] if text else []), **kwargs)


class Desc(_Descriptive, tag="desc"):
    """``<desc>``: a long description.

    Parameters
    ----------
    text : str, optional
        The description text. Defaults to empty.
    **kwargs
        Style, core and other SVG attributes in Python spelling.

    See Also
    --------
    Title : A short, tooltip-style description.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Desc("A red square"))
    '<desc>A red square</desc>'
    """


class Title(_Descriptive, tag="title"):
    """``<title>``: a short, tooltip-style description.

    Parameters
    ----------
    text : str, optional
        The title text. Defaults to empty.
    **kwargs
        Style, core and other SVG attributes in Python spelling.

    See Also
    --------
    Desc : A longer description.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Title("Square"))
    '<title>Square</title>'
    """


class Metadata(CoreAttributes, tag="metadata", category=Category.DESCRIPTIVE, content=ContentModel.MIXED):
    """``<metadata>``: arbitrary content, usually RDF in a foreign namespace.

    Parameters
    ----------
    *children : Element or str
        The content.
    **kwargs
        Core and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Metadata("licensed"))
    '<metadata>licensed</metadata>'
    """

    def __init__(self, *children: Child, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
