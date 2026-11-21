"""
Constants for ``svgwriter.formats.inkscape``: attribute names, defaults and conventions of Inkscape files.
"""

from __future__ import annotations

from typing import Final

from ..._internal._constants import INKSCAPE_LABEL

__all__ = [
    "ANGLE_PRECISION",
    "ARC_ATTRIBUTES",
    "ARC_TYPES",
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
    "HANDLE_REACH",
    "HORIZONTAL",
    "LABEL",
    "LAYER",
    "MAX_ARC_SEGMENTS",
    "MIN_RADIUS",
    "NAMEDVIEW_TAG",
    "QUARTER_TURNS",
    "SHAPE_TYPE",
    "STAR_ATTRIBUTES",
    "STAR_FLATSIDED",
    "STAR_RANDOMIZED",
    "STAR_ROUNDED",
    "TRUE",
    "UP",
    "VERTICAL",
]

LABEL: Final = INKSCAPE_LABEL
GROUP_MODE: Final = "inkscape:groupmode"
LAYER: Final = "layer"

SHAPE_TYPE: Final = "sodipodi:type"
STAR_FLATSIDED: Final = "inkscape:flatsided"
STAR_ROUNDED: Final = "inkscape:rounded"
STAR_RANDOMIZED: Final = "inkscape:randomized"
STAR_ATTRIBUTES: Final = {
    "cx": "sodipodi:cx",
    "cy": "sodipodi:cy",
    "r1": "sodipodi:r1",
    "r2": "sodipodi:r2",
    "arg1": "sodipodi:arg1",
    "arg2": "sodipodi:arg2",
    "sides": "sodipodi:sides",
}
ARC_ATTRIBUTES: Final = {
    "cx": "sodipodi:cx",
    "cy": "sodipodi:cy",
    "rx": "sodipodi:rx",
    "ry": "sodipodi:ry",
    "start": "sodipodi:start",
    "end": "sodipodi:end",
    "kind": "sodipodi:arc-type",
}
ARC_TYPES: Final = ("slice", "arc", "chord")
TRUE: Final = "true"
FALSE: Final = "false"
UP: Final = -90.0
ANGLE_PRECISION: Final = 9
HALF_TURN_DEGREES: Final = 180.0
QUARTER_TURNS: Final = 4
MAX_ARC_SEGMENTS: Final = 4
MIN_RADIUS: Final = 1e-8
HANDLE_REACH: Final = 100000.0

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
