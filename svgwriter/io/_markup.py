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
from ._constants import NAMESPACE_DECLARATION, RANK

__all__ = ["default_namespaces", "inline_content", "open_text", "ordered", "used_namespaces"]


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


def used_namespaces(element: Element) -> tuple[set[str], set[str], set[str]]:
    """Prefixes of ``prefix:name`` attributes, URIs of ``{uri}name`` attributes and foreign element URIs in the tree."""
    prefixes: set[str] = set()
    attribute_uris: set[str] = set()
    element_uris: set[str] = set()
    for node in element.iter():
        namespace = getattr(node, "namespace", None)
        if namespace and namespace != SVG_NS:
            element_uris.add(namespace)
        for key in node.attributes:
            if key.startswith("{"):
                attribute_uris.add(key[1:].partition("}")[0])
            elif ":" in key:
                prefix = key.partition(":")[0]
                if prefix != NAMESPACE_DECLARATION:
                    prefixes.add(prefix)
    return prefixes, attribute_uris, element_uris



@contextmanager
def open_text(path: AnyPath, encoding: str) -> Generator[IO[str], None, None]:
    """Open *path* for writing text with LF line endings."""
    with open(path, "w", encoding=encoding, newline="\n") as handle:
        yield handle
