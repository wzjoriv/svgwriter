"""
Recording a scene for baking: each element's state at every sample time, and the copies the baked document is built from.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.attributes.names import PRESENTATION_ATTRIBUTES
from ...model.attributes.style import Style
from ...model.attributes.values import format_value
from ...model.elements.animation import AnimationElement
from ...model.elements.core import Element

if TYPE_CHECKING:
    from ...document import Document
    from ...model.transform.matrix import Matrix

__all__ = ["Record", "Tape", "label", "walk"]


@dataclass(frozen=True)
class Record:
    """One element at one moment: attribute and property values as text, transform, text nodes and parent."""

    values: dict[str, str]
    loose: str
    matrix: Matrix | None
    text: tuple[str, ...]
    parent: int | None
    previous: int | None


def walk(element: Element) -> Iterator[Element]:
    """*element* and its descendants in document order, leaving out animation elements."""
    yield element
    for child in element.children:
        if isinstance(child, Element) and not isinstance(child, AnimationElement):
            yield from walk(child)


def label(element: Element) -> str:
    """``<tag#id>`` for messages."""
    return f"<{element.tag}{'#' + element.id if element.id else ''}>"


def _transform_attribute(element: Element) -> str | None:
    return getattr(type(element), "transform_attribute", None)


def _record(element: Element, previous: int | None) -> Record:
    skip = {"style", _transform_attribute(element)}
    values = {name: format_value(value) for name, value in element.attributes.items() if name not in skip}
    style = element.attributes.get("style")
    declarations = Style(str(style)) if style is not None else Style()
    loose = []
    for name, value in declarations.items():
        if name in PRESENTATION_ATTRIBUTES:
            values[name] = str(value)
        else:
            loose.append(f"{name}:{value}")
    matrix = element.t if _transform_attribute(element) else None  # type: ignore[attr-defined]
    text = tuple(child for child in element.children if isinstance(child, str))
    parent = id(element.parent) if element.parent is not None else None
    return Record(values, ";".join(loose), matrix, text, parent, previous)


class Tape:
    """Every element's record at every sample, and baked copies of the elements, keyed by ``id()``."""

    def __init__(self, document: Document) -> None:
        self.document = document
        self.frames: list[dict[int, Record]] = []
        self.elements: dict[int, Element] = {}
        self.baked: dict[int, Element] = {}
        self.added: list[tuple[int, Element]] = []
        self.root: Element | None = None

    def capture(self) -> None:
        """Record the document's current state as the next frame."""
        records: dict[int, Record] = {}
        previous: dict[int, int] = {}
        for element in walk(self.document.root):
            key = id(element)
            parent = id(element.parent) if element.parent is not None else None
            records[key] = _record(element, previous.get(parent) if parent is not None else None)
            if parent is not None:
                previous[parent] = key
            if key in self.elements:
                continue
            self.elements[key] = element
            if not self.frames and self.root is None:
                self.root = self._copy(element)
            elif self.frames and key not in self.baked and parent in self.baked:
                self.added.append((key, self._copy(element)))
        self.frames.append(records)

    def _copy(self, element: Element) -> Element:
        copy = element.clone()
        for original, duplicate in zip(walk(element), walk(copy), strict=True):
            self.baked.setdefault(id(original), duplicate)
        return copy

    def place(self) -> None:
        """Put the copies of elements that appeared after the first frame into the baked tree."""
        for key, copy in self.added:
            first = next(frame[key] for frame in self.frames if key in frame)
            parent = self.baked[first.parent]  # type: ignore[index]
            index = 0
            if first.previous is not None and first.previous in self.baked:
                sibling = self.baked[first.previous]
                index = next(i for i, child in enumerate(parent.children) if child is sibling) + 1
            parent.insert(index, copy)

    def series(self, key: int) -> tuple[list[Record], list[bool]]:
        """The element's record at every frame, held over the frames where it is absent, and its presence."""
        present = [key in frame for frame in self.frames]
        first = next(frame[key] for frame in self.frames if key in frame)
        held, last = [], first
        for frame in self.frames:
            last = frame.get(key, last)
            held.append(last)
        return held, present

    def inherited(self, index: int, key: int | None, name: str) -> str | None:
        """The value of property *name* an element would inherit at frame *index*, from its recorded ancestors."""
        frame = self.frames[index]
        while key is not None and key in frame:
            record = frame[key]
            if name in record.values:
                return record.values[name]
            key = record.parent
        return None
