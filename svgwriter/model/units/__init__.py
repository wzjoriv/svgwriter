"""
Lengths, angles and their units: ``svg.mm(5)``, ``5 * svg.inch``, ``svg.Length``, ``svg.Angle``, ``svg.Quantity``.

Units SVG has no suffix for (metres, feet, miles, ...) are written in the nearest SVG unit, so every value
converts back to SVG.
"""

from ._factories import (
    AngleUnit,
    LengthUnit,
    angle,
    cm,
    deg,
    em,
    ex,
    ft,
    furlong,
    grad,
    inch,
    km,
    length,
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
from .angles import Angle
from .lengths import Length, LengthLike, Unit
from .quantities import Quantity

__all__ = [
    "Angle",
    "AngleUnit",
    "Length",
    "LengthLike",
    "LengthUnit",
    "Quantity",
    "Unit",
    "angle",
    "cm",
    "deg",
    "em",
    "ex",
    "ft",
    "furlong",
    "grad",
    "inch",
    "km",
    "length",
    "m",
    "mi",
    "mil",
    "mm",
    "nmi",
    "pc",
    "percent",
    "pt",
    "px",
    "q",
    "rad",
    "turn",
    "um",
    "yd",
]
