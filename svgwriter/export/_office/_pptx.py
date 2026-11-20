"""
PowerPoint slides as DrawingML shapes, written and read with python-pptx.
"""

from __future__ import annotations

import io
import math
from typing import TYPE_CHECKING, Any

from . import require
from ._constants import (
    A_NS,
    ALPHA_SCALE,
    ASCENT,
    BLANK_LAYOUT,
    DEFAULT_TEXT_PT,
    EMU_PER_POINT,
    EMU_PER_UNIT,
    GENERIC_FONTS,
    LINE_HEIGHT,
    POINTS_PER_UNIT,
    ROUND_RECT_ADJUST,
    SLIDE_MAX_EMU,
    SLIDE_MIN_EMU,
)

if TYPE_CHECKING:
    from ...color.color import Color
    from ...document import Document
    from ...pathdata.data import PathData
    from .._flatten import Item


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


def write_pptx(document: Document) -> bytes:
    """Write the deck; see :func:`svgwriter.export._office.pptx`."""
    presentation_module = require("pptx")
    from .._flatten import flatten

    scene = flatten(document, handled=frozenset({"image"}), text=True)
    scale = _emu_scale(scene.width, scene.height)
    deck = presentation_module.Presentation()
    deck.slide_width, deck.slide_height = round(scene.width * scale), round(scene.height * scale)
    slide = deck.slides.add_slide(deck.slide_layouts[BLANK_LAYOUT])
    for image in _images(document):
        box = image.bounds()
        if box is not None and image.pixels is not None:
            slide.shapes.add_picture(io.BytesIO(image.encode("png")), round(box.x * scale), round(box.y * scale),
                                     round(box.width * scale), round(box.height * scale))
    for item in scene.items:
        _freeform(slide, item, scale)
    for run in scene.texts:
        _textbox(slide, run, scale)
    buffer = io.BytesIO()
    deck.save(buffer)
    return buffer.getvalue()


def _textbox(slide: Any, run: Any, scale: float) -> None:
    """One text run as an editable, unwrapped text box whose first baseline sits on the run's baseline."""
    from pptx.dml.color import RGBColor
    from pptx.enum.text import MSO_AUTO_SIZE
    from pptx.util import Pt

    matrix = run.matrix
    stretch = math.sqrt(abs(matrix.determinant))
    size = run.size * stretch
    angle = math.degrees(math.atan2(matrix.b, matrix.a))
    width, height = max(run.width * stretch, 1.0), size * LINE_HEIGHT
    turn = math.radians(angle)
    # Top-left of the unrotated box in the run's frame, then its centre on the page (PowerPoint turns about it).
    top = -size * ASCENT
    centre_x = matrix.e + math.cos(turn) * width / 2 - math.sin(turn) * (top + height / 2)
    centre_y = matrix.f + math.sin(turn) * width / 2 + math.cos(turn) * (top + height / 2)
    box = slide.shapes.add_textbox(round((centre_x - width / 2) * scale), round((centre_y - height / 2) * scale),
                                   round(width * scale), round(height * scale))
    box.rotation = angle
    frame = box.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.word_wrap = False
    frame.auto_size = MSO_AUTO_SIZE.NONE
    text_run = frame.paragraphs[0].add_run()
    text_run.text = run.text
    font = text_run.font
    font.size = Pt(size * scale / EMU_PER_POINT)
    font.name = _office_family(run.family)
    font.bold, font.italic = run.bold, run.italic
    if run.fill is not None:
        font.color.rgb = RGBColor(*run.fill.uint8[:3])
        if run.opacity < 1:
            fill = font.color._color._xClr  # noqa: SLF001 - python-pptx exposes no text alpha
            alpha = fill.makeelement(_a("alpha"), {"val": str(round(run.opacity * ALPHA_SCALE))})
            fill.append(alpha)


def _office_family(family: str) -> str:
    """The first concrete font of a CSS family list, with generic names mapped to common Office fonts."""
    first = family.split(",")[0].strip().strip("'\"")
    return GENERIC_FONTS.get(first.lower(), first)


def _images(document: Document) -> list[Any]:
    from ...elements.structure import Image

    return [element for element in document.root.iter() if isinstance(element, Image)]


def _freeform(slide: Any, item: Item, scale: float) -> None:
    """One flattened item as a custom-geometry shape with its paints."""
    shapes_module = require("pptx.enum.shapes")
    oxml = require("pptx.oxml")
    from ...ops._skia import from_skia, to_skia

    data = from_skia(to_skia(item.data))
    box = data.bbox
    if box is None:
        return
    left, top = box.x * scale, box.y * scale
    width, height = max(box.width * scale, 1.0), max(box.height * scale, 1.0)
    shape = slide.shapes.add_shape(shapes_module.MSO_SHAPE.RECTANGLE, round(left), round(top), round(width),
                                   round(height))
    element = shape._element
    style = element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}style")
    if style is not None:
        element.remove(style)
    properties = element.spPr
    preset = properties.find(_a("prstGeom"))
    geometry = oxml.parse_xml(_geometry_xml(data, box.x, box.y, scale, round(width), round(height)))
    properties.replace(preset, geometry)
    _paint(shape.fill, item.fill, item.fill_opacity)
    if item.stroke is None or item.stroke_width <= 0:
        shape.line.fill.background()
    else:
        _paint(shape.line.fill, item.stroke, item.stroke_opacity)
        shape.line.width = round(item.stroke_width * scale)


def _geometry_xml(data: PathData, x0: float, y0: float, scale: float, width: int, height: int) -> str:
    """``<a:custGeom>`` with the path in shape-local EMU."""
    from ...pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo

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


def read_pptx(data: bytes, index: int) -> Document:
    """Read one slide; see :func:`svgwriter.export._office.read_pptx`."""
    presentation_module = require("pptx")
    from ...document import Document

    deck = presentation_module.Presentation(io.BytesIO(data))
    slides = list(deck.slides)
    if not -len(slides) <= index < len(slides):
        raise IndexError(f"the deck has {len(slides)} slides, not slide {index}")
    doc = Document(deck.slide_width / EMU_PER_UNIT, deck.slide_height / EMU_PER_UNIT)
    for shape in slides[index].shapes:
        _read_shape(doc, shape)
    return doc


def _read_shape(parent: Any, shape: Any) -> None:
    """Add *shape* (recursing into groups) to *parent* as native elements."""
    from ...elements.structure import Group, Image, Pixels

    left, top = (shape.left or 0) / EMU_PER_UNIT, (shape.top or 0) / EMU_PER_UNIT
    width, height = (shape.width or 0) / EMU_PER_UNIT, (shape.height or 0) / EMU_PER_UNIT
    if shape.shape_type is not None and shape.shape_type == require("pptx.enum.shapes").MSO_SHAPE_TYPE.GROUP:
        group = parent.add(Group())
        for child in shape.shapes:
            _read_shape(group, child)
        return
    element: Any = None
    if hasattr(shape, "image"):
        pixels = Pixels.decode(shape.image.blob)
        element = Image(pixels.rgba(), left, top, width, height, preserve_aspect_ratio="none")
    else:
        element = _outline(shape, left, top, width, height)
    if element is not None:
        if shape.rotation:
            element.rotate(shape.rotation, about=(left + width / 2, top + height / 2))
        parent.add(element)
    text = _text(shape, left, top)
    if text is not None:
        if shape.rotation:
            text.rotate(shape.rotation, about=(left + width / 2, top + height / 2))
        parent.add(text)


def _outline(shape: Any, left: float, top: float, width: float, height: float) -> Any:
    """A preset or custom shape as a ``<path>`` with its fill and outline, or None."""
    from ...elements.shapes import Path

    properties = getattr(shape._element, "spPr", None)
    if properties is None:
        return None
    custom, preset = properties.find(_a("custGeom")), properties.find(_a("prstGeom"))
    if custom is not None:
        data = _custom_path(custom, left, top, width, height)
    elif preset is not None:
        data = _preset_path(preset.get("prst"), left, top, width, height)
    else:
        return None
    if data is None:
        return None
    path = Path(data)
    fill, stroke = _solid(properties.find(_a("solidFill"))), None
    line = properties.find(_a("ln"))
    if line is not None and line.find(_a("noFill")) is None:
        stroke = _solid(line.find(_a("solidFill")))
        if stroke is not None:
            path.set("stroke-width", int(line.get("w", EMU_PER_UNIT)) / EMU_PER_UNIT)
    if fill is None and stroke is None:
        return None
    path.set("fill", fill if fill is not None else "none")
    if stroke is not None:
        path.set("stroke", stroke)
    return path


def _solid(fill: Any) -> Any:
    """The color of an ``<a:solidFill>`` with an explicit RGB value, alpha included, or None."""
    from ...color.color import Color

    rgb = fill.find(_a("srgbClr")) if fill is not None else None
    if rgb is None:
        return None
    alpha = rgb.find(_a("alpha"))
    value = Color.parse("#" + rgb.get("val"))
    return value.with_alpha(int(alpha.get("val")) / ALPHA_SCALE) if alpha is not None else value


def _custom_path(geometry: Any, left: float, top: float, width: float, height: float) -> Any:
    """The ``<a:path>`` commands mapped from their own ``w``/``h`` box onto the shape."""
    from ...pathdata.builder import PathBuilder

    builder = PathBuilder()
    for path in geometry.iter(_a("path")):
        scale_x = width / int(path.get("w", 1) or 1)
        scale_y = height / int(path.get("h", 1) or 1)
        for command in path:
            points = [(left + int(p.get("x")) * scale_x, top + int(p.get("y")) * scale_y)
                      for p in command.iter(_a("pt"))]
            name = command.tag.rsplit("}", 1)[-1]
            if name == "moveTo":
                builder.move_to(*points[0])
            elif name == "lnTo":
                builder.line_to(*points[0])
            elif name == "cubicBezTo":
                builder.curve_to(*points[0], *points[1], *points[2])
            elif name == "quadBezTo":
                builder.quad_to(*points[0], *points[1])
            elif name == "close":
                builder.close()
    data = builder.build()
    return data if len(data) else None


def _preset_path(name: str | None, left: float, top: float, width: float, height: float) -> Any:
    """Outlines of the common preset shapes."""
    from ...elements.shapes import Ellipse, Line, Rect

    if name == "rect":
        return Rect(left, top, width, height).local_outline()
    if name == "roundRect":
        radius = min(width, height) * ROUND_RECT_ADJUST / ALPHA_SCALE
        return Rect(left, top, width, height, rx=radius).local_outline()
    if name == "ellipse":
        return Ellipse(left + width / 2, top + height / 2, width / 2, height / 2).local_outline()
    if name in ("line", "straightConnector1"):
        return Line(left, top, left + width, top + height).local_outline()
    return None


def _text(shape: Any, left: float, top: float) -> Any:
    """A text box's paragraphs as one ``<text>`` per line, with font, weight, style and colour, or None."""
    from ...elements.structure import Group
    from ...elements.text import Text

    if not getattr(shape, "has_text_frame", False) or not shape.text_frame.text.strip():
        return None
    frame = shape.text_frame
    group = Group()
    left += (frame.margin_left or 0) / EMU_PER_UNIT
    line_top = top + (frame.margin_top or 0) / EMU_PER_UNIT
    for paragraph in frame.paragraphs:
        font = next((run.font for run in paragraph.runs if run.font.size is not None), None)
        size_units = (font.size.pt if font is not None else DEFAULT_TEXT_PT) / POINTS_PER_UNIT
        if paragraph.text:
            text = Text(paragraph.text, x=left, y=line_top + size_units * ASCENT,
                        font_size=math.floor(size_units * 100) / 100)
            if font is not None:
                _text_style(text, font)
            group.add(text)
        line_top += size_units * LINE_HEIGHT
    return group if len(group) else None


def _text_style(text: Any, font: Any) -> None:
    """Copy a python-pptx run font's family, weight, style and explicit colour onto *text*."""
    if font.name:
        text.set("font-family", font.name)
    if font.bold:
        text.set("font-weight", "bold")
    if font.italic:
        text.set("font-style", "italic")
    properties = font._rPr  # noqa: SLF001 - the colour's alpha is not exposed
    color = _solid(properties.find(_a("solidFill"))) if properties is not None else None
    if color is not None:
        text.set("fill", color)
