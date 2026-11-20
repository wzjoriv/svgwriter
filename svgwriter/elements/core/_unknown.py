"""
Elements without a dedicated class.
"""

from __future__ import annotations

from typing import Any

from ._categories import ContentModel
from ._element import Child, Element

__all__ = ["UnknownElement"]


class UnknownElement(Element, content=ContentModel.MIXED):
    """An element without a dedicated class (foreign or unsupported).

    Parameters
    ----------
    tag : str
        The element name.
    *children : Element or str
        Child elements and text.
    namespace : str, optional
        Namespace URI of the element. Defaults to None.
    **kwargs
        Attributes, as for :class:`~svgwriter.Element`.

    Examples
    --------
    >>> from svgwriter.elements.core import UnknownElement
    >>> UnknownElement("widget", "hi").tag
    'widget'
    """

    namespace: str | None = None

    def __init__(self, tag: str, *children: Child, namespace: str | None = None, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self.tag = tag  # type: ignore[misc]
        self.namespace = namespace
