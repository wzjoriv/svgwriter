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
elements
    One class per SVG 1.1 element (``structure``, ``shapes``, ``text``,
    ``fonts``, ``paint``, ``clip``, ``filters``, ``animation``).
attributes
    Lengths and units, ``viewBox``, ``preserveAspectRatio``, inline styles
    and style sheets, IRI references, attribute-name mapping.
pathdata
    Path data: commands, parsing, serialization, transforms, arc math,
    ``PathBuilder`` and node arrays.
transform
    Affine matrices and transform lists.
color
    Color keywords and syntaxes and the ``<paint>`` type.
io
    Serialization options, writers (string, file, stream, async) and the
    parser.
builder
    Composite shapes (star, gear, arrow) and effects (shadow, glow).
theme
    Palettes, fonts and role styles applied as CSS classes (``Theme``).
ops
    Boolean operations, text outlines, measurement, rendering and image
    compositing (skia).
export
    Format registry by name or extension: vector (SVG, PDF, TikZ, EPS),
    raster (PNG, JPEG, WebP, BMP, GIF, PPM, ICO, ICNS), plotter (DXF, HPGL,
    G-code) and Excalidraw; ``svg.export.register`` adds more.
video
    Frame rendering through a pluggable renderer and encoding with ffmpeg.
cli
    The ``python -m svgwriter`` command line.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import export, ops, theme, video
from ._document.sizes import SIZES, page_size, register_size, unregister_size
from .aliases import *  # noqa: E402, F403
from .aliases import __all__ as _aliases_all  # noqa: E402
from .aliases import filter as filter  # noqa: A004, E402
from .aliases import set as set
from .attributes import (
    IRI,
    Align,
    Angle,
    FuncIRI,
    Length,
    MeetOrSlice,
    PreserveAspectRatio,
    Style,
    StyleSheet,
    Unit,
    ViewBox,
    cm,
    deg,
    em,
    grad,
    inch,
    mm,
    percent,
    pt,
    px,
    rad,
    turn,
)
from .builder import SHAPES, drawing, drop_shadow, shape_factory
from .color import Color, PaintKeyword, parse_color, parse_paint
from .document import Document
from .elements import *  # noqa: F403
from .elements import __all__ as _elements_all
from .elements.presets import animation
from .io.writer import SerializeOptions, to_string, write
from .ops import interpolate, register_font, register_interpolator, text_to_path, unregister_interpolator
from .pathdata import BBox, PathBuilder, PathData
from .theme import THEMES, Theme
from .transform import Matrix, Point, Transform
from .video import FFmpegNotFoundError, Scene, register_renderer

if TYPE_CHECKING:
    from ._internal._latex import latex
    from .io import write_async
    from .io.parser import Strictness, SVGParseError, parse, parse_file

__version__ = "1.3.0"
__author__ = "Josue N Rivera"

_LAZY = {
    "latex": ("_internal._latex", "latex"),
    "parse": ("io.parser", "parse"),
    "parse_file": ("io.parser", "parse_file"),
    "Strictness": ("io.parser", "Strictness"),
    "SVGParseError": ("io.parser", "SVGParseError"),
    "write_async": ("io", "write_async"),
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(name for name in {*globals(), *_LAZY} if not name.startswith("_") and name not in _TYPING_NAMES)


__all__ = [
    "BBox",
    "FFmpegNotFoundError",
    "IRI",
    "Point",
    "SVGParseError",
    "SHAPES",
    "SIZES",
    "Scene",
    "Align",
    "Color",
    "Document",
    "FuncIRI",
    "Length",
    "Matrix",
    "MeetOrSlice",
    "PaintKeyword",
    "PathBuilder",
    "PathData",
    "PreserveAspectRatio",
    "SerializeOptions",
    "Strictness",
    "Style",
    "StyleSheet",
    "THEMES",
    "Theme",
    "Transform",
    "Unit",
    "ViewBox",
    "__author__",
    "__version__",
    "cm",
    "drawing",
    "drop_shadow",
    "em",
    "inch",
    "Angle",
    "deg",
    "grad",
    "rad",
    "turn",
    "mm",
    "animation",
    "interpolate",
    "page_size",
    "latex",
    "parse",
    "register_font",
    "register_size",
    "register_interpolator",
    "parse_color",
    "parse_file",
    "parse_paint",
    "export",
    "ops",
    "percent",
    "pt",
    "px",
    "register_renderer",
    "shape_factory",
    "text_to_path",
    "theme",
    "unregister_interpolator",
    "unregister_size",
    "to_string",
    "video",
    "write",
    "write_async",
    *_elements_all,
    *_aliases_all,
]
