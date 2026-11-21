"""
Which scene owns a document: lets ``element.animate.<behavior>`` find the scene that runs it.
"""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from ...model.elements.core import Element

__all__ = ["adopt", "scene_of"]

_OWNERS: Final[weakref.WeakValueDictionary[int, Any]] = weakref.WeakValueDictionary()


def adopt(root: Element, scene: Any) -> None:
    """Record *scene* as the owner of the document whose root element is *root*."""
    _OWNERS[id(root)] = scene


def scene_of(element: Element) -> Any | None:
    """The scene whose document holds *element*, or None."""
    root = element.root()
    scene = _OWNERS.get(id(root))
    return scene if scene is not None and scene.document.root is root else None
