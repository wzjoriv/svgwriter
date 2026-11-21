"""
Inkscape's document units and export hints (``inkscape:document-units``, ``inkscape:export-xdpi``, ...).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..elements.core import Element
from ._constants import DOCUMENT_UNITS, EXPORT_FILENAME, EXPORT_XDPI, EXPORT_YDPI
from .guides import namedview

__all__ = ["ExportHints", "export_hints", "set_export_hints"]


@dataclass(frozen=True)
class ExportHints:
    """What Inkscape remembers about exporting a document.

    Parameters
    ----------
    dpi : float, optional
        Resolution of the last bitmap export (``inkscape:export-xdpi``); raster
        exports use it when no ``scale``, ``dpi`` or ``size`` is given.
        Defaults to None.
    filename : str, optional
        Where Inkscape last exported (``inkscape:export-filename``). Defaults to None.
    units : str, optional
        The unit Inkscape's rulers and toolbars show (``inkscape:document-units``
        on ``<sodipodi:namedview>``), such as ``"mm"``. Defaults to None.

    See Also
    --------
    svgwriter.Document.export_hints : Read or set them on a document.

    Examples
    --------
    >>> from svgwriter.inkscape import ExportHints
    >>> ExportHints(dpi=300).dpi
    300
    """

    dpi: float | None = None
    filename: str | None = None
    units: str | None = None


def export_hints(root: Element) -> ExportHints:
    """The export hints stored on a document's ``<svg>`` and ``<sodipodi:namedview>``.

    Parameters
    ----------
    root : Element
        A document's ``<svg>``.

    Returns
    -------
    ExportHints
        Fields are None where the file has no hint.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.inkscape.export_hints(svg.svg(inkscape_export_xdpi=150)).dpi
    150.0
    """
    dpi = root.attributes.get(EXPORT_XDPI)
    filename = root.attributes.get(EXPORT_FILENAME)
    view = namedview(root)
    units = None if view is None else view.attributes.get(DOCUMENT_UNITS)
    return ExportHints(None if dpi is None else float(dpi), None if filename is None else str(filename),
                       None if units is None else str(units))


def set_export_hints(root: Element, hints: ExportHints) -> None:
    """Store export hints on a document; None fields remove the hint.

    Parameters
    ----------
    root : Element
        A document's ``<svg>``.
    hints : ExportHints
        The hints to write.

    Examples
    --------
    >>> import svgwriter as svg
    >>> root = svg.svg()
    >>> svg.inkscape.set_export_hints(root, svg.inkscape.ExportHints(dpi=300, units="mm"))
    >>> root.attributes["inkscape:export-xdpi"], svg.inkscape.export_hints(root).units
    (300, 'mm')
    """
    for name, value in ((EXPORT_XDPI, hints.dpi), (EXPORT_YDPI, hints.dpi), (EXPORT_FILENAME, hints.filename)):
        if value is None:
            root.attributes.pop(name, None)
        else:
            root.attributes[name] = value
    view = namedview(root, create=hints.units is not None)
    if view is not None:
        if hints.units is None:
            view.attributes.pop(DOCUMENT_UNITS, None)
        else:
            view.attributes[DOCUMENT_UNITS] = hints.units
