"""
Small serialization helpers: attribute order, namespaces, inline content and text files.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import IO, Any

from .._internal._constants import SVG_NS, XLINK_NS
from .._internal._typing import AnyPath
from ..elements.core import Category, Element
from ._constants import RANK

__all__ = ["default_namespaces", "inline_content", "open_text", "ordered", "uses_xlink"]


def ordered(attributes: dict[str, Any]) -> list[tuple[str, Any]]:
    """``id`` and geometry first (in a conventional order), then the rest as inserted."""
    lead = sorted((item for item in attributes.items() if item[0] in RANK), key=lambda item: RANK[item[0]])
    return lead + [item for item in attributes.items() if item[0] not in RANK]


def default_namespaces() -> dict[str, str]:
    """The ``xmlns`` and ``xmlns:xlink`` declarations written on a root."""
    return {"xmlns": SVG_NS, "xmlns:xlink": XLINK_NS}



def inline_content(element: Element) -> bool:
    """Whether *element*'s children are written on one line (text content or mixed text)."""
    return element.category is Category.TEXT_CONTENT or any(isinstance(c, str) for c in element.children)


def uses_xlink(element: Element) -> bool:
    """Whether any element in the tree has an ``xlink:`` attribute."""
    return any(key.startswith("xlink:") for node in element.iter() for key in node.attributes)



@contextmanager
def open_text(path: AnyPath, encoding: str) -> Generator[IO[str], None, None]:
    """Open *path* for writing text with LF line endings."""
    with open(path, "w", encoding=encoding, newline="\n") as handle:
        yield handle
