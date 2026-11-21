"""
Inkscape layers (``<g inkscape:groupmode="layer">``) and readable element names (``inkscape:label``).
"""

from __future__ import annotations

from typing import Any

from ..elements.core import Element
from ..elements.structure import Group
from ._constants import GROUP_MODE, LABEL, LAYER

__all__ = ["by_label", "is_layer", "layers", "new_layer"]


def is_layer(element: Element) -> bool:
    """Whether *element* is an Inkscape layer or sublayer.

    Parameters
    ----------
    element : Element
        Any element.

    Returns
    -------
    bool
        True for a ``<g>`` with ``inkscape:groupmode="layer"``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.inkscape.is_layer(svg.inkscape.new_layer("Sky")), svg.inkscape.is_layer(svg.group())
    (True, False)
    """
    return element.tag == "g" and element.attributes.get(GROUP_MODE) == LAYER


def new_layer(label: str, **kwargs: Any) -> Group:
    """Build an empty Inkscape layer.

    Parameters
    ----------
    label : str
        The name Inkscape shows in its Layers panel (``inkscape:label``).
    **kwargs
        Attributes for the ``<g>``.

    Returns
    -------
    Group
        The layer.

    See Also
    --------
    svgwriter.Document.layer : Find or add a layer of a document.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.inkscape.new_layer("Sky").label
    'Sky'
    """
    layer = Group(**kwargs)
    layer.attributes.update({GROUP_MODE: LAYER, LABEL: label})
    return layer


def layers(root: Element) -> dict[str, Group]:
    """Every layer and sublayer under *root*, in document order, by label.

    Parameters
    ----------
    root : Element
        Where to look, usually a document's ``<svg>``.

    Returns
    -------
    dict of str to Group
        Layers by ``inkscape:label`` (their id when unlabelled); when two share a
        label, the first one is kept.

    Examples
    --------
    >>> import svgwriter as svg
    >>> root = svg.svg(svg.inkscape.new_layer("Back"), svg.inkscape.new_layer("Front"))
    >>> list(svg.inkscape.layers(root))
    ['Back', 'Front']
    """
    found: dict[str, Group] = {}
    for element in root.iter("g"):
        if is_layer(element):
            found.setdefault(element.label or element.id or "", element)  # type: ignore[arg-type]
    return found


def by_label(root: Element, label: str) -> Element | None:
    """The element named *label* (``inkscape:label``) under *root*, if exactly one has it.

    Parameters
    ----------
    root : Element
        Where to look.
    label : str
        The readable name.

    Returns
    -------
    Element or None
        The element, or None when no element has that label.

    Raises
    ------
    KeyError
        If several elements share the label.

    Examples
    --------
    >>> import svgwriter as svg
    >>> root = svg.svg(svg.rect(0, 0, 1, 1, inkscape_label="Logo"))
    >>> svg.inkscape.by_label(root, "Logo").tag
    'rect'
    """
    matches = [element for element in root.iter() if element.attributes.get(LABEL) == label]
    if len(matches) > 1:
        raise KeyError(f"{len(matches)} elements are labelled {label!r}; give them ids to tell them apart")
    return matches[0] if matches else None
