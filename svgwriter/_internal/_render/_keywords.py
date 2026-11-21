"""
CSS-wide keywords made explicit on a render copy: ``inherit`` and ``currentColor`` become concrete values,
and CSS Color 4 colours (``oklch()``, ``color(display-p3 ...)``, alpha forms) become sRGB hex.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._constants import COLOR_OPACITIES, COLOR_PROPERTIES, CURRENT_COLOR, INHERIT, LEGACY_COLOR_RE, NONE

if TYPE_CHECKING:
    from ...elements.core import Element

__all__ = ["resolve_colors", "resolve_keywords"]


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
    >>> from svgwriter._internal._render._keywords import resolve_keywords
    >>> group = svg.Group(svg.Rect(fill="currentColor", stroke="inherit"), color="red", stroke="blue")
    >>> resolve_keywords(group)
    >>> rect = group[0]
    >>> str(rect.get("fill")), str(rect.get("stroke"))
    ('red', 'blue')
    """
    from ...attributes.cascade import computed

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


def resolve_colors(root: Element) -> None:
    """Write every colour property in a syntax SVG 1.1 renderers read, in place on a render copy.

    Colours beyond hex, comma ``rgb()`` and keywords (``oklch()``, ``lab()``, ``hsl()``,
    ``color(display-p3 ...)``, alpha forms) become sRGB hex, clipped to the sRGB gamut, and their
    alpha multiplies the matching opacity property.

    Parameters
    ----------
    root : Element
        A render copy with resolved styles and keywords; it is changed in place.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._keywords import resolve_colors
    >>> rect = svg.Rect(fill="oklch(0.7 0.3 145 / 0.5)", fill_opacity=0.5)
    >>> resolve_colors(rect)
    >>> rect.get("fill"), rect.get("fill-opacity")
    ('#00c800', 0.25)
    """
    from ...color.color import Color

    for element in root.iter():
        for name in COLOR_PROPERTIES & element.attributes.keys():
            text = _text(element.attributes[name])
            if text == NONE or LEGACY_COLOR_RE.match(text):
                continue
            try:
                color = Color.parse(text)
            except ValueError:
                continue
            element.attributes[name] = color.opaque.hex
            opacity = COLOR_OPACITIES.get(name)
            if color.a < 1.0 and opacity is not None:
                element.attributes[opacity] = float(_text(element.attributes.get(opacity, 1.0))) * color.a
