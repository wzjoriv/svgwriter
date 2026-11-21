"""
PowerPoint slides in: DrawingML shapes, pictures, text boxes and equations as native elements.
"""

from __future__ import annotations

import io
import math
from typing import TYPE_CHECKING, Any

from . import require
from ._anim_apply import apply_effect
from ._constants import (
    ALPHA_SCALE,
    ASCENT,
    DEFAULT_TEXT_PT,
    EMU_PER_UNIT,
    LINE_HEIGHT,
    M_NS,
    POINTS_PER_UNIT,
    PPTX_SIZE_SCALE,
    ROUND_RECT_ADJUST,
)
from ._drawingml import read_gradient, read_line_style
from ._pptx import _a
from ._pptx_timing_read import read_timing

if TYPE_CHECKING:
    from ...document import Document


def read_pptx(data: bytes, index: int | None) -> Document | list[Document]:
    """Read one slide, or every slide when *index* is None; see :func:`svgwriter.export._office.read_pptx`."""
    presentation_module = require("pptx")
    from ...document import Document

    deck = presentation_module.Presentation(io.BytesIO(data))
    slides = list(deck.slides)
    if index is not None and not -len(slides) <= index < len(slides):
        raise IndexError(f"the deck has {len(slides)} slides, not slide {index}")
    docs = []
    for slide in slides if index is None else [slides[index]]:
        size = (deck.slide_width / EMU_PER_UNIT, deck.slide_height / EMU_PER_UNIT)
        doc = Document(*size)
        drawn: dict[int, list[Any]] = {}
        for shape in slide.shapes:
            _read_shape(doc, shape, drawn)
        for spid, effect in read_timing(slide._element, size):
            for element in drawn.get(spid, []):
                apply_effect(element, effect)
        docs.append(doc)
    return docs if index is None else docs[0]


def _read_shape(parent: Any, shape: Any, drawn: dict[int, list[Any]]) -> None:
    """Add *shape* (recursing into groups) to *parent* as native elements, listed in *drawn* by shape id."""
    from ...elements.structure import A, Group, Image, Pixels

    left, top = (shape.left or 0) / EMU_PER_UNIT, (shape.top or 0) / EMU_PER_UNIT
    width, height = (shape.width or 0) / EMU_PER_UNIT, (shape.height or 0) / EMU_PER_UNIT
    if shape.shape_type is not None and shape.shape_type == require("pptx.enum.shapes").MSO_SHAPE_TYPE.GROUP:
        group = parent.add(Group())
        drawn.setdefault(shape.shape_id, []).append(group)
        for child in shape.shapes:
            _read_shape(group, child, drawn)
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
        address = _link(shape)
        parent.add(A(element, href=address) if address else element)
        drawn.setdefault(shape.shape_id, []).append(element)
    text = _text(shape, left, top)
    if text is not None:
        if shape.rotation:
            text.rotate(shape.rotation, about=(left + width / 2, top + height / 2))
        parent.add(text)
        drawn.setdefault(shape.shape_id, []).append(text)


def _link(shape: Any) -> str | None:
    """The hyperlink a click on *shape* follows, or None."""
    try:
        return shape.click_action.hyperlink.address
    except (AttributeError, KeyError, ValueError):
        return None


def _outline(shape: Any, left: float, top: float, width: float, height: float) -> Any:
    """A preset or custom shape as a ``<path>`` with its fill and outline, or None."""
    properties = getattr(shape._element, "spPr", None)
    return outline(properties, left, top, width, height) if properties is not None else None


def outline(properties: Any, left: float, top: float, width: float, height: float) -> Any:
    """The geometry of a DrawingML ``spPr`` as a ``<path>`` with its solid or gradient fill and outline.

    Parameters
    ----------
    properties : lxml element
        The shape properties holding a preset or custom geometry.
    left, top, width, height : float
        The shape's box on the page, in user units.

    Returns
    -------
    Path or None
        None when the geometry is unknown or nothing is painted.

    Examples
    --------
    >>> from lxml import etree
    >>> from svgwriter.export._office._pptx_read import outline
    >>> sp = etree.fromstring('<p:spPr xmlns:p="urn:p" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
    ...     '<a:prstGeom prst="rect"/><a:solidFill><a:srgbClr val="FF0000"/></a:solidFill></p:spPr>')
    >>> outline(sp, 0, 0, 10, 5).get("fill").hex
    '#ff0000'
    """
    from ...elements.shapes import Path

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
    shade = properties.find(_a("gradFill"))
    if fill is None and shade is not None:
        fill = read_gradient(shade, left, top, width, height)
    line = properties.find(_a("ln"))
    if line is not None and line.find(_a("noFill")) is None:
        stroke = _solid(line.find(_a("solidFill")))
        if stroke is not None:
            stroke_width = int(line.get("w", EMU_PER_UNIT)) / EMU_PER_UNIT
            path.set("stroke-width", stroke_width)
            read_line_style(path, line, stroke_width)
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

    if not getattr(shape, "has_text_frame", False) or not (
            shape.text_frame.text.strip() or _math_text(shape.text_frame._txBody)):
        return None
    frame = shape.text_frame
    group = Group()
    if not frame.text.strip():
        return _equation(shape, left, top, group)
    left += (frame.margin_left or 0) / EMU_PER_UNIT
    line_top = top + (frame.margin_top or 0) / EMU_PER_UNIT
    for paragraph in frame.paragraphs:
        font = next((run.font for run in paragraph.runs if run.font.size is not None), None)
        size_units = (font.size.pt if font is not None else DEFAULT_TEXT_PT) / POINTS_PER_UNIT
        content = paragraph.text
        if content:
            text = Text(content, x=left, y=line_top + size_units * ASCENT,
                        font_size=math.floor(size_units * 100) / 100)
            if font is not None:
                _text_style(text, font)
            group.add(text)
        line_top += size_units * LINE_HEIGHT
    return group if len(group) else None


def _equation(shape: Any, left: float, top: float, group: Any) -> Any:
    """An equation box as its characters centred in the box, at the equation's own size."""
    from ...elements.text import Text

    body = shape.text_frame._txBody  # noqa: SLF001 - equations are not exposed by python-pptx
    sizes = [int(node.get("sz")) for node in body.iter(_a("rPr")) if node.get("sz")]
    size_units = (sizes[0] / PPTX_SIZE_SCALE if sizes else DEFAULT_TEXT_PT) / POINTS_PER_UNIT
    centre_x = left + shape.width / EMU_PER_UNIT / 2
    centre_y = top + shape.height / EMU_PER_UNIT / 2
    group.add(Text(_math_text(body), x=centre_x, y=centre_y + size_units * (ASCENT - LINE_HEIGHT / 2),
                   font_size=math.floor(size_units * 100) / 100, text_anchor="middle"))
    return group


def _math_text(element: Any) -> str:
    """The characters of the Office equations under *element*, in reading order, without their layout."""
    return "".join(node.text or "" for node in element.iter(f"{{{M_NS}}}t"))


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
