"""
Page units: lengths given in Python resolve against the unit a physically sized document counts in.

A root sized ``210mm`` with a 210-wide ``viewBox`` counts user units in millimetres. Writing
``width="20mm"`` inside it would make browsers scale the millimetres a second time (20 CSS
millimetres are 75.6 user units), so lengths given in Python become plain user units of the page:
``svg.mm(20)`` is 20 there, ``svg.inch(1)`` is 25.4. Text read from SVG files keeps its SVG meaning.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._constants import PAGE_LENGTH_DIGITS

if TYPE_CHECKING:
    from ..attributes.length import Length, Unit
    from ..elements.core import Element

__all__ = ["adopt_page_lengths", "page_length", "page_unit", "to_page"]


def page_unit(element: Element) -> tuple[Unit, float] | None:
    """The physical unit the document holding *element* counts in, and user units per that unit.

    Parameters
    ----------
    element : Element
        Any element; its root is inspected.

    Returns
    -------
    (Unit, float) or None
        The root width's unit and the ``viewBox`` width per unit of it, or None when the root is not an
        ``<svg>`` sized in ``mm``, ``cm``, ``Q``, ``in``, ``pt`` or ``pc`` with a ``viewBox``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._page import page_unit
    >>> page_unit(svg.Document(size="a4").root)
    (<Unit.MM: 'mm'>, 1.0)
    >>> page_unit(svg.Document(100, 50).root) is None
    True
    """
    from ..attributes.length import Length, Unit

    root = element.root()
    width, box = root.attributes.get("width"), root.attributes.get("viewBox")
    if root.tag != "svg" or width is None or box is None:
        return None
    try:
        length = Length.parse(width)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not length.absolute or length.unit in (Unit.NONE, Unit.PX) or not length.value:
        return None
    return length.unit, float(root.view_box.width) / length.value  # type: ignore[attr-defined]


def page_length(value: Length, unit: tuple[Unit, float] | None) -> Length | float:
    """*value* in user units of a page counting in *unit*; relative lengths and user units pass through.

    Parameters
    ----------
    value : Length
        The length.
    unit : (Unit, float) or None
        The page unit from :func:`page_unit`; None keeps SVG's own meaning.

    Returns
    -------
    Length or float
        A plain number of page user units, or `value` itself.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._page import page_length
    >>> page_length(svg.inch(1), (svg.Unit.MM, 1.0))
    25.4
    >>> page_length(svg.Length(2, "em"), (svg.Unit.MM, 1.0))
    Length(value=2.0, unit=<Unit.EM: 'em'>)
    """
    from ..attributes.length import Unit

    if unit is None or value.unit is Unit.NONE or not value.absolute:
        return value
    return round(value.to(unit[0]).value * unit[1], PAGE_LENGTH_DIGITS)


def to_page(value: Any, element: Element) -> float:
    """A length given in Python as user units of the document holding *element*.

    Parameters
    ----------
    value : float, str or Length
        A number of user units or a length.
    element : Element
        Where the length is used.

    Returns
    -------
    float
        Page user units in a physically sized document, else SVG user units (96 per inch).

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._page import to_page
    >>> doc = svg.Document(size="a4")
    >>> to_page(svg.cm(2), doc.root), to_page(svg.cm(2), svg.group()) == svg.cm(2).to_user_units()
    (20.0, True)
    """
    from ..attributes.length import Length

    length = Length.parse(value)
    resolved = page_length(length, page_unit(element))
    return resolved if isinstance(resolved, float) else resolved.to_user_units()


def _converted(key: str, value: object, unit: tuple[Unit, float]) -> object:
    from ..attributes.length import Length
    from ..attributes.names import LENGTH_ATTRIBUTES

    if key in LENGTH_ATTRIBUTES and isinstance(value, Length):
        return page_length(value, unit)
    return value


def adopt_page_lengths(subtree: Element, unit: tuple[Unit, float] | None) -> None:
    """Turn the Python lengths in *subtree* into user units of a page counting in *unit*.

    Lengths held as `Length` objects (``svg.mm(20)``, ``"20mm"`` passed to an attribute) convert in
    attributes and inline styles; attribute text read from a file keeps its SVG meaning.

    Parameters
    ----------
    subtree : Element
        The element joining the page, with its descendants.
    unit : (Unit, float) or None
        The page unit from :func:`page_unit`; None leaves everything as it is.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(size="a4")
    >>> doc.rect(0, 0, svg.mm(20), svg.inch(1)).attributes["height"]
    25.4
    """
    if unit is None:
        return
    from ..attributes.style import Style

    for element in subtree.iter():
        for key, value in list(element.attributes.items()):
            if isinstance(value, Style):
                for name, declared in list(value.items()):
                    value[name] = _converted(name, declared, unit)
            else:
                element.attributes[key] = _converted(key, value, unit)
