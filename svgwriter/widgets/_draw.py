"""
Calling a drawing function with control values, and carrying a new drawing over onto an old one in place.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from typing import Any

from ..document import Document
from ..model.elements.core import Element

__all__ = ["arguments", "draw", "morph"]


def _takes_document(function: Callable[..., Any], names: Mapping[str, Any]) -> bool:
    try:
        parameters = list(inspect.signature(function).parameters.values())
    except (TypeError, ValueError):
        return False
    first = parameters[0] if parameters else None
    return (first is not None and first.name not in names and first.default is inspect.Parameter.empty
            and first.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD))


def arguments(controls: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    """The keyword arguments for *values*, each converted by its control."""
    return {name: controls[name].argument(value) for name, value in values.items()}


def draw(function: Callable[..., Any], kwargs: Mapping[str, Any]) -> Document:
    """Call *function* and return its drawing as a document.

    A function whose first parameter is not a control receives a new :class:`~svgwriter.Document` there, as
    project entries do; it may draw into it and return nothing. A returned element is placed in a document
    sized to its content.
    """
    page = Document() if _takes_document(function, kwargs) else None
    result = function(page, **kwargs) if page is not None else function(**kwargs)
    if isinstance(result, Document):
        return result
    if isinstance(result, Element):
        if result.tag == "svg" and result.parent is None:
            return Document(root=result)  # type: ignore[arg-type]
        document = Document()
        document += result
        return document
    if result is None and page is not None:
        return page
    name = getattr(function, "__name__", "the function")
    raise TypeError(f"{name} returned {type(result).__name__}; expected a Document or an Element")


def _matches(old: Any, new: Any) -> bool:
    if isinstance(old, str) or isinstance(new, str):
        return isinstance(old, str) and isinstance(new, str)
    return old.tag == new.tag


def morph(target: Element, source: Element, *, attributes: bool = True) -> None:
    """Make *target* look like *source*, keeping *target*'s elements wherever the two trees have the same shape.

    Matching children keep their identity and only take the new attributes and text, so a scene's baker sees
    attribute changes it can interpolate. Where the shapes differ, *target*'s children are replaced.
    """
    if attributes:
        target.attributes.clear()
        target.attributes.update(source.attributes)
    old, new = target.children, list(source.children)
    if len(old) == len(new) and all(_matches(a, b) for a, b in zip(old, new, strict=True)):
        for position, (a, b) in enumerate(zip(old, new, strict=True)):
            if isinstance(a, str):
                old[position] = b
            else:
                morph(a, b)
        return
    for child in list(old):
        target.remove(child)
    for child in new:
        target.append(child)
