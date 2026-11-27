"""Attribute value types: view boxes, styles, references, names. Lengths and angles are in `svgwriter.model.units`."""

from __future__ import annotations

from .descriptors import Attr
from .names import CAMEL_CASE_ATTRIBUTES, PRESENTATION_ATTRIBUTES, py_name, svg_name
from .protocols import SupportsSVG, TextSink
from .reference import IRI, FuncIRI, parse_func_iri
from .style import Style, StyleLike, StyleSheet
from .values import format_value
from .viewbox import Align, MeetOrSlice, PreserveAspectRatio, ViewBox

__all__ = [
    "CAMEL_CASE_ATTRIBUTES",
    "IRI",
    "PRESENTATION_ATTRIBUTES",
    "Align",
    "Attr",
    "FuncIRI",
    "MeetOrSlice",
    "PreserveAspectRatio",
    "Style",
    "StyleLike",
    "StyleSheet",
    "SupportsSVG",
    "TextSink",
    "ViewBox",
    "format_value",
    "parse_func_iri",
    "py_name",
    "svg_name",
]
