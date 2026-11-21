"""
CSS-wide keywords made explicit on a render copy: ``inherit`` and ``currentColor`` become concrete values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._constants import COLOR_PROPERTIES, CURRENT_COLOR, INHERIT

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["resolve_keywords"]


def _text(value: object) -> str:
    return str(value.svg_value() if hasattr(value, "svg_value") else value).strip()


def resolve_keywords(root: Element) -> None:
    """Replace ``inherit`` by the parent's computed value and ``currentColor`` by the computed ``color``.

    Works in place on a tree whose styles are already presentation attributes (see
    :func:`~svgwriter.attributes.cascade.resolve_styles`), so renderers that know neither
    keyword for a property (``stop-color`` and ``stop-opacity`` above all) draw it right.
    An ``inherit`` with nothing to inherit is dropped, leaving the initial value.

    Parameters
    ----------
    root : Element
        A render copy; it is changed in place.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._keywords import resolve_keywords
    >>> group = svg.Group(svg.Rect(fill="currentColor", stroke="inherit"), color="red", stroke="blue")
    >>> resolve_keywords(group)
    >>> rect = group[0]
    >>> str(rect.get("fill")), str(rect.get("stroke"))
    ('red', 'blue')
    """
    from ..attributes.cascade import computed

    for element in list(root.iter()):
        for name, value in list(element.attributes.items()):
            text = _text(value)
            if text == INHERIT:
                inherited = computed(element.parent, name, None, []) if element.parent is not None else None
                if inherited is None or _text(inherited) == INHERIT:
                    del element.attributes[name]
                else:
                    element.attributes[name] = inherited
            elif text == CURRENT_COLOR and name in COLOR_PROPERTIES:
                element.attributes[name] = computed(element, "color", "black", [])
