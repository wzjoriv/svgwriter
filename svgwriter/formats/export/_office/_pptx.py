"""
PowerPoint slides out: DrawingML shapes, pictures, text boxes and equations, written with python-pptx.
"""

from __future__ import annotations

import io
import math
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from xml.sax.saxutils import escape

from . import require
from ._constants import (
    A14_NS,
    A_NS,
    ALPHA_SCALE,
    ASCENT,
    BLANK_LAYOUT,
    EMU_PER_POINT,
    EMU_PER_UNIT,
    GENERIC_FONTS,
    LINE_HEIGHT,
    MATH_FONT,
    MC_NS,
    SLIDE_MAX_EMU,
    SLIDE_MIN_EMU,
)
from ._drawingml import gradient_xml, line_style

if TYPE_CHECKING:
    from ...._internal._flat._flatten import Item
    from ....document import Document
    from ....model.color.color import Color
    from ....model.pathdata.data import PathData
    from ._layout import Equation


def _a(tag: str) -> str:
    return f"{{{A_NS}}}{tag}"


def _emu_scale(width: float, height: float) -> float:
    """EMU per user unit, adjusted so the slide stays within PowerPoint's size limits."""
    scale = float(EMU_PER_UNIT)
    longest, shortest = max(width, height) * scale, min(width, height) * scale
    if longest > SLIDE_MAX_EMU:
        scale *= SLIDE_MAX_EMU / longest
    elif shortest and shortest < SLIDE_MIN_EMU:
        scale *= min(SLIDE_MIN_EMU / shortest, SLIDE_MAX_EMU / longest)
    return scale


@dataclass(frozen=True)
class _Place:
    """Maps page user units onto a slide: EMU per unit and the offset that centres the page."""

    scale: float
    dx: float = 0.0
    dy: float = 0.0

    def emu(self, x: float, y: float, width: float, height: float) -> tuple[int, int, int, int]:
        return (round((x + self.dx) * self.scale), round((y + self.dy) * self.scale),
                round(width * self.scale), round(height * self.scale))


def write_pptx(documents: list[Document]) -> bytes:
    """Write the deck, one slide per document; see :func:`svgwriter.formats.export._office.pptx`."""
    presentation_module = require("pptx")
    from ...._internal._flat._flatten import flatten
    from ...._internal._render._layers import pixel_box
    from ._layout import split_equations
    from ._pptx_anim import slide_animations

    animations = [slide_animations(document) for document in documents]
    parts = [split_equations(animated.document) for animated in animations]
    documents = [rest for rest, _ in parts]
    scenes = [flatten(document, handled=frozenset({"image"}), text=True) for document in documents]
    width, height = max(scene.width for scene in scenes), max(scene.height for scene in scenes)
    scale = _emu_scale(width, height)
    deck = presentation_module.Presentation()
    deck.slide_width, deck.slide_height = round(width * scale), round(height * scale)
    dropped: list[str] = []
    for scene, (_, equations), animated in zip(scenes, parts, animations, strict=True):
        slide = deck.slides.add_slide(deck.slide_layouts[BLANK_LAYOUT])
        place = _Place(scale, (width - scene.width) / 2, (height - scene.height) / 2)
        for item in scene.painted():
            if isinstance(item, tuple):
                image, matrix = item
                picture = slide.shapes.add_picture(io.BytesIO(image.encode("png")),
                                                   *place.emu(*pixel_box(image, matrix)))
                animated.attach(picture, image)
            else:
                animated.attach(_freeform(slide, item, place), item.source)
        for run in scene.texts:
            animated.attach(_textbox(slide, run, place), run.source)
        for equation in equations:
            _equation(slide, equation, place)
        dropped += animated.write(slide, (width, height))
    if dropped:
        warnings.warn(f"PowerPoint cannot play these animations, dropped: {', '.join(sorted(set(dropped)))}",
                      stacklevel=3)
    buffer = io.BytesIO()
    deck.save(buffer)
    return buffer.getvalue()


def _textbox(slide: Any, run: Any, place: _Place) -> Any:
    """One text run as an editable, unwrapped text box whose first baseline sits on the run's baseline."""
    from pptx.dml.color import RGBColor
    from pptx.enum.text import MSO_AUTO_SIZE
    from pptx.util import Pt

    left, top, width, height, angle, size = text_box(run)
    box = slide.shapes.add_textbox(*place.emu(left, top, width, height))
    box.rotation = angle
    frame = box.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.word_wrap = False
    frame.auto_size = MSO_AUTO_SIZE.NONE
    text_run = frame.paragraphs[0].add_run()
    text_run.text = run.text
    font = text_run.font
    font.size = Pt(size * place.scale / EMU_PER_POINT)
    font.name = _office_family(run.family)
    font.bold, font.italic = run.bold, run.italic
    if run.fill is not None:
        font.color.rgb = RGBColor(*run.fill.uint8[:3])
        if run.opacity < 1:
            fill = font.color._color._xClr  # noqa: SLF001 - python-pptx exposes no text alpha
            alpha = fill.makeelement(_a("alpha"), {"val": str(round(run.opacity * ALPHA_SCALE))})
            fill.append(alpha)
    return box


def text_box(run: Any) -> tuple[float, float, float, float, float, float]:
    """The unrotated box of a text run whose first baseline sits on the run's baseline, turned about its centre.

    Parameters
    ----------
    run : TextRun
        A run from a flattened scene.

    Returns
    -------
    tuple of float
        Left, top, width and height of the box before rotation, the rotation
        in degrees and the font size, all in page user units.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._flat._flatten import flatten
    >>> from svgwriter.formats.export._office._pptx import text_box
    >>> doc = svg.Document(100, 40)
    >>> _ = doc.text("Hi", x=10, y=30, font_size=20)
    >>> left, top, width, height, angle, size = text_box(flatten(doc, text=True).texts[0])
    >>> (left, round(top, 1), angle, size)
    (10.0, 12.0, 0.0, 20.0)
    """
    matrix = run.matrix
    stretch = math.sqrt(abs(matrix.determinant))
    size = run.size * stretch
    angle = math.degrees(math.atan2(matrix.b, matrix.a))
    width, height = max(run.width * stretch, 1.0), size * LINE_HEIGHT
    turn = math.radians(angle)
    top = -size * ASCENT
    centre_x = matrix.e + math.cos(turn) * width / 2 - math.sin(turn) * (top + height / 2)
    centre_y = matrix.f + math.sin(turn) * width / 2 + math.cos(turn) * (top + height / 2)
    return centre_x - width / 2, centre_y - height / 2, width, height, angle, size


def _equation(slide: Any, equation: Equation, place: _Place) -> None:
    """An editable PowerPoint equation centred in the box of the LaTeX group it replaces."""
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
    from pptx.oxml import parse_xml

    from ._omml import latex_to_omml

    size = round(equation.size * place.scale / EMU_PER_POINT * 100)
    box = slide.shapes.add_textbox(*place.emu(equation.x, equation.y, equation.width, equation.height))
    box.name = "Equation"
    frame = box.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.word_wrap = False
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.CENTER
    properties = f'<a:rPr xmlns:a="{A_NS}" lang="en-US" sz="{size}"><a:latin typeface="{MATH_FONT}"/></a:rPr>'
    math = latex_to_omml(equation.source, properties)
    paragraph._p.append(parse_xml(
        f'<mc:AlternateContent xmlns:mc="{MC_NS}" xmlns:a14="{A14_NS}"><mc:Choice Requires="a14"><a14:m>{math}'
        f'</a14:m></mc:Choice><mc:Fallback><a:r xmlns:a="{A_NS}"><a:rPr lang="en-US" sz="{size}"/>'
        f"<a:t>{escape(equation.source)}</a:t></a:r></mc:Fallback></mc:AlternateContent>"))


def _office_family(family: str) -> str:
    """The first concrete font of a CSS family list, with generic names mapped to common Office fonts."""
    first = family.split(",")[0].strip().strip("'\"")
    return GENERIC_FONTS.get(first.lower(), first)


def _freeform(slide: Any, item: Item, place: _Place) -> Any:
    """One flattened item as a custom-geometry shape with its paints; None when it has no extent."""
    shapes_module = require("pptx.enum.shapes")
    oxml = require("pptx.oxml")
    from ....ops import from_skia, to_skia

    data = from_skia(to_skia(item.data))
    box = data.bbox
    if box is None:
        return None
    scale = place.scale
    left, top, _, _ = place.emu(box.x, box.y, 0, 0)
    width, height = max(box.width * scale, 1.0), max(box.height * scale, 1.0)
    shape = slide.shapes.add_shape(shapes_module.MSO_SHAPE.RECTANGLE, left, top, round(width), round(height))
    element = shape._element
    style = element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}style")
    if style is not None:
        element.remove(style)
    properties = element.spPr
    preset = properties.find(_a("prstGeom"))
    geometry = oxml.parse_xml(_geometry_xml(data, box.x, box.y, scale, round(width), round(height)))
    properties.replace(preset, geometry)
    _paint(shape.fill, item.fill, item.fill_opacity)
    solid = properties.find(_a("solidFill"))
    if item.shading is not None and solid is not None:
        properties.replace(solid, oxml.parse_xml(gradient_xml(item.shading, box, item.fill_opacity)))
    if item.stroke is None or item.stroke_width <= 0:
        shape.line.fill.background()
    else:
        _paint(shape.line.fill, item.stroke, item.stroke_opacity)
        shape.line.width = round(item.stroke_width * scale)
        line_style(properties.find(_a("ln")), item.stroke_width, item.dashes, item.linecap, item.linejoin,
                   item.miter_limit)
    if item.link:
        shape.click_action.hyperlink.address = item.link
    return shape


def _geometry_xml(data: PathData, x0: float, y0: float, scale: float, width: int, height: int) -> str:
    """``<a:custGeom>`` with the path in shape-local EMU."""
    from ....model.pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo

    def point(x: float, y: float) -> str:
        return f'<a:pt x="{round((x - x0) * scale)}" y="{round((y - y0) * scale)}"/>'

    parts = []
    for command in data:
        if isinstance(command, MoveTo):
            parts.append(f"<a:moveTo>{point(command.x, command.y)}</a:moveTo>")
        elif isinstance(command, LineTo):
            parts.append(f"<a:lnTo>{point(command.x, command.y)}</a:lnTo>")
        elif isinstance(command, QuadTo):
            parts.append(f"<a:quadBezTo>{point(command.x1, command.y1)}{point(command.x, command.y)}</a:quadBezTo>")
        elif isinstance(command, CurveTo):
            parts.append(f"<a:cubicBezTo>{point(command.x1, command.y1)}{point(command.x2, command.y2)}"
                         f"{point(command.x, command.y)}</a:cubicBezTo>")
        elif isinstance(command, ClosePath):
            parts.append("<a:close/>")
    return (f'<a:custGeom xmlns:a="{A_NS}"><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
            f'<a:rect l="0" t="0" r="r" b="b"/><a:pathLst><a:path w="{width}" h="{height}">'
            f'{"".join(parts)}</a:path></a:pathLst></a:custGeom>')


def _paint(fill: Any, color: Color | None, opacity: float) -> None:
    """A solid fill (with alpha) or none."""
    dml = require("pptx.dml.color")
    if color is None or opacity <= 0:
        fill.background()
        return
    fill.solid()
    red, green, blue, _ = color.uint8
    fill.fore_color.rgb = dml.RGBColor(red, green, blue)
    if opacity < 1:
        solid = fill._xPr.find(_a("solidFill")) if hasattr(fill, "_xPr") else None
        target = solid.find(_a("srgbClr")) if solid is not None else None
        if target is not None:
            alpha = target.makeelement(_a("alpha"), {"val": str(round(opacity * ALPHA_SCALE))})
            target.append(alpha)
