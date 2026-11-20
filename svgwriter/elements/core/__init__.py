"""
The ``Element`` base, its registry and machinery, typed containers and the fallback element.
"""

from __future__ import annotations

from ._container import Container, GraphicsContainer
from ._element import AttrValue, Category, Child, ContentModel, Element
from ._factory import ElementFactory
from ._unknown import UnknownElement

__all__ = [
    "AttrValue",
    "Category",
    "Child",
    "Container",
    "ContentModel",
    "Element",
    "ElementFactory",
    "GraphicsContainer",
    "UnknownElement",
]
