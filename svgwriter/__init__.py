"""svgwriter: write SVG 1.1 documents from Python.

Every SVG 1.1 element is a class with keyword arguments for its attributes
(``stroke_width`` becomes ``stroke-width``, ``class_`` becomes ``class``),
also available under a lowercase alias (``svg.circle is svg.Circle``).
Documents and containers have shortcut methods that build, add and return
elements; operators compose them. Documents serialize to pretty or compact
text and parse back into the same object model.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(120, 80)
>>> grad = svg.LinearGradient.horizontal("gold", "tomato")
>>> with doc.group(stroke="black", stroke_width=2) as g:
...     _ = doc.rect(10, 10, 100, 60, rx=8, fill=grad)
...     _ = doc.text("Hello", x=60, y=45, text_anchor="middle")
>>> g += svg.circle(60, 40, 3)
>>> svg.parse(doc.to_string()).find(svg.Rect).get("rx")
'8'

Sub-packages
------------
model
    The object model: ``elements``, ``attributes``, ``color``, ``pathdata``,
    ``transform``, ``layout``, ``theme`` and ``batch`` (``svg.Rect``, ``svg.Theme``,
    ``svg.batch.circles``).
catalog
    Ready-made content: ``builder``, ``patterns``, ``gradients``, ``filters``,
    ``markers``, ``effects``, ``preset`` and ``fonts``
    (``fill=svg.patterns.stripes()``, ``svg.FontBuilder``).
formats
    Files: ``export`` (format registry by name or extension), ``io``
    (writers and the parser) and ``inkscape``.
motion
    ``video``: scenes, frame rendering and encoding with ffmpeg.
tools
    ``cli`` (the ``python -m svgwriter`` command line), ``project`` (design
    projects) and ``widgets`` (notebook panels and sweeps).
ops
    Boolean operations, text outlines, measurement, rendering and image
    compositing (skia).

Every sub-package listed above by name is also an attribute of this
package (``svg.patterns``, ``svg.export``, ``svg.video``), except ``cli``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import errors, ops
from ._document.sizes import PageSize, page_size, size
from ._internal._constants import SUGGESTIONS as _SUGGESTIONS
from ._internal._registry import Registry
from .aliases import *  # noqa: E402, F403
from .aliases import __all__ as _aliases_all  # noqa: E402
from .aliases import filter as filter  # noqa: A004, E402
from .aliases import set as set
from .catalog import builder as builder
from .catalog import effects, filters, fonts, gradients, markers, patterns, preset
from .catalog.builder import drawing
from .catalog.fonts import FontBuilder
from .document import Document
from .formats import Format, export, inkscape
from .formats import io as io
from .formats.io.writer import SerializeOptions, to_string, write
from .model import attributes as attributes
from .model import batch as batch
from .model import color as color
from .model import elements as elements
from .model import layout, theme
from .model import pathdata as pathdata
from .model import transform as transform
from .model.attributes import (
    IRI,
    Align,
    Angle,
    FuncIRI,
    Length,
    MeetOrSlice,
    PreserveAspectRatio,
    Quantity,
    Style,
    StyleSheet,
    Unit,
    ViewBox,
    cm,
    deg,
    em,
    ft,
    grad,
    inch,
    m,
    mm,
    percent,
    pt,
    px,
    q,
    rad,
    turn,
)
from .model.attributes.units import angle, length
from .model.color import Color, PaintKeyword, parse_color, parse_paint
from .model.elements import *  # noqa: F403
from .model.elements import __all__ as _elements_all
from .model.layout import Grid, HStack, Spacer, VStack
from .model.pathdata import BBox, PathBuilder, PathData
from .model.theme import Theme, themes
from .model.transform import Matrix, Point, Transform
from .motion import video
from .motion.video import Scene, renderers
from .ops import (
    Typeface,
    distribute,
    interpolate,
    register_font,
    register_interpolator,
    text_to_path,
    unregister_interpolator,
)
from .tools import project, widgets
from .tools.project import Project
from .tools.widgets import interact, sweep

if TYPE_CHECKING:
    from ._internal._latex import latex
    from .formats.io import write_async
    from .formats.io.parser import Strictness, parse, parse_file

__version__ = "2.4.0"
__author__ = "Josue N Rivera"

_LAZY = {
    "latex": ("_internal._latex", "latex"),
    "parse": ("formats.io.parser", "parse"),
    "parse_file": ("formats.io.parser", "parse_file"),
    "Strictness": ("formats.io.parser", "Strictness"),
    "write_async": ("formats.io", "write_async"),
}


_TYPING_NAMES = frozenset({"Any", "TYPE_CHECKING", "annotations"})


def __getattr__(name: str) -> Any:
    """Import the parser and async helpers on first use."""
    if name in _LAZY:
        import importlib

        module_name, attribute = _LAZY[name]
        value = getattr(importlib.import_module(f".{module_name}", __name__), attribute)
        globals()[name] = value
        return value
    import difflib

    close = difflib.get_close_matches(name, __dir__(), n=_SUGGESTIONS)
    hint = f"; did you mean {' or '.join(map(repr, close))}?" if close else ""
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}{hint}")


def __dir__() -> list[str]:
    return sorted(name for name in {*globals(), *_LAZY} if not name.startswith("_") and name not in _TYPING_NAMES)


__all__ = [
    "BBox",
    "FontBuilder",
    "IRI",
    "Point",
    "Scene",
    "Align",
    "Color",
    "Document",
    "FuncIRI",
    "Length",
    "Matrix",
    "MeetOrSlice",
    "PageSize",
    "PaintKeyword",
    "PathBuilder",
    "PathData",
    "PreserveAspectRatio",
    "Quantity",
    "SerializeOptions",
    "Strictness",
    "Style",
    "StyleSheet",
    "themes",
    "Theme",
    "Transform",
    "Typeface",
    "Unit",
    "ViewBox",
    "__author__",
    "__version__",
    "cm",
    "drawing",
    "em",
    "inch",
    "ft",
    "m",
    "q",
    "length",
    "angle",
    "Angle",
    "deg",
    "grad",
    "rad",
    "turn",
    "mm",
    "distribute",
    "interpolate",
    "page_size",
    "latex",
    "parse",
    "register_font",
    "register_interpolator",
    "parse_color",
    "parse_file",
    "parse_paint",
    "export",
    "effects",
    "filters",
    "fonts",
    "gradients",
    "inkscape",
    "layout",
    "Grid",
    "HStack",
    "Spacer",
    "VStack",
    "markers",
    "ops",
    "patterns",
    "preset",
    "project",
    "Project",
    "percent",
    "pt",
    "px",
    "renderers",
    "Registry",
    "errors",
    "Format",
    "size",
    "text_to_path",
    "theme",
    "unregister_interpolator",
    "to_string",
    "video",
    "widgets",
    "interact",
    "sweep",
    "write",
    "write_async",
    *_elements_all,
    *_aliases_all,
]
