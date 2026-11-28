"""
Constants for ``svgwriter.formats.inkscape``: attribute names, defaults and conventions of Inkscape files.
"""

from __future__ import annotations

from typing import Final

from ..._internal._constants import INKSCAPE_LABEL

__all__ = [
    "CONNECTION_END",
    "CONNECTION_START",
    "CONNECTOR_CURVATURE",
    "CONNECTOR_TYPE",
    "CONNECTOR_TYPES",
    "DEFAULT_CONNECTOR",
    "DOCUMENT_UNITS",
    "EXPORT_FILENAME",
    "EXPORT_XDPI",
    "EXPORT_YDPI",
    "FALSE",
    "GROUP_MODE",
    "GUIDE_COLOR",
    "GUIDE_LOCKED",
    "GUIDE_ORIENTATION",
    "GUIDE_POSITION",
    "GUIDE_PRECISION",
    "GUIDE_TAG",
    "HALF_TURN_DEGREES",
    "HORIZONTAL",
    "LABEL",
    "LAYER",
    "NAMEDVIEW_TAG",
    "TRUE",
    "VERTICAL",
]

LABEL: Final = INKSCAPE_LABEL
GROUP_MODE: Final = "inkscape:groupmode"
LAYER: Final = "layer"

TRUE: Final = "true"
FALSE: Final = "false"
HALF_TURN_DEGREES: Final = 180.0

CONNECTOR_TYPE: Final = "inkscape:connector-type"
CONNECTION_START: Final = "inkscape:connection-start"
CONNECTION_END: Final = "inkscape:connection-end"
CONNECTOR_CURVATURE: Final = "inkscape:connector-curvature"
CONNECTOR_TYPES: Final = ("polyline", "orthogonal")
DEFAULT_CONNECTOR: Final = "polyline"

NAMEDVIEW_TAG: Final = "namedview"
GUIDE_TAG: Final = "guide"
GUIDE_POSITION: Final = "position"
GUIDE_ORIENTATION: Final = "orientation"
GUIDE_COLOR: Final = "inkscape:color"
GUIDE_LOCKED: Final = "inkscape:locked"
GUIDE_PRECISION: Final = 9
HORIZONTAL: Final = 0.0
VERTICAL: Final = 90.0

DOCUMENT_UNITS: Final = "inkscape:document-units"
EXPORT_XDPI: Final = "inkscape:export-xdpi"
EXPORT_YDPI: Final = "inkscape:export-ydpi"
EXPORT_FILENAME: Final = "inkscape:export-filename"
