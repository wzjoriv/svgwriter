"""Attribute value types: lengths, view boxes, styles, references, names."""

from __future__ import annotations

from .angle import Angle
from .descriptors import Attr
from .length import Length, LengthLike, Unit
from .names import CAMEL_CASE_ATTRIBUTES, PRESENTATION_ATTRIBUTES, py_name, svg_name
from .protocols import SupportsSVG, TextSink
from .quantity import Quantity
from .reference import IRI, FuncIRI, parse_func_iri
from .style import Style, StyleLike, StyleSheet
from .units import (
    AngleUnit,
    LengthUnit,
    cm,
    deg,
    em,
    ex,
    ft,
    furlong,
    grad,
    inch,
    km,
    m,
    mi,
    mil,
    mm,
    nmi,
    pc,
    percent,
    pt,
    px,
    q,
    rad,
    turn,
    um,
    yd,
)
from .values import format_value
from .viewbox import Align, MeetOrSlice, PreserveAspectRatio, ViewBox

__all__ = [
    "Angle",
    "AngleUnit",
    "deg",
    "grad",
    "rad",
    "turn",
    "CAMEL_CASE_ATTRIBUTES",
    "IRI",
    "PRESENTATION_ATTRIBUTES",
    "Align",
    "Attr",
    "FuncIRI",
    "Length",
    "LengthLike",
    "LengthUnit",
    "MeetOrSlice",
    "PreserveAspectRatio",
    "Quantity",
    "Style",
    "StyleLike",
    "StyleSheet",
    "SupportsSVG",
    "TextSink",
    "Unit",
    "ViewBox",
    "cm",
    "em",
    "ex",
    "format_value",
    "ft",
    "furlong",
    "km",
    "mi",
    "mil",
    "nmi",
    "um",
    "yd",
    "inch",
    "m",
    "mm",
    "pc",
    "parse_func_iri",
    "percent",
    "pt",
    "px",
    "q",
    "py_name",
    "svg_name",
]
