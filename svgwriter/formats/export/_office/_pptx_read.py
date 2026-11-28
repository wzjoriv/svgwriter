"""
PowerPoint slides in: DrawingML shapes, pictures, text boxes and equations as native elements.
"""

from __future__ import annotations

import colorsys
import io
import math
import warnings
from typing import TYPE_CHECKING, Any

from . import require
from ._anim_apply import apply_effect
from ._constants import (
    ALPHA_SCALE,
    ASCENT,
    DEFAULT_TEXT_PT,
    EMU_PER_UNIT,
    HORIZONTAL_ALIGNS,
    LINE_HEIGHT,
    M_NS,
    P_NS,
    POINTS_PER_UNIT,
    PPTX_SIZE_SCALE,
    ROUND_RECT_ADJUST,
    SCHEME_ALIASES,
    STYLE_LINE_WIDTH,
    THEME_RELATIONSHIP,
    VERTICAL_ANCHORS,
)
from ._drawingml import read_gradient, read_line_style
from ._pptx import _a
from ._pptx_presets import preset_points
from ._pptx_timing_read import read_timing, read_triggers

if TYPE_CHECKING:
    from ....document import Document


_SCHEMES: dict[int, dict[str, str]] = {}
"""Theme colour schemes read so far, by slide master part."""

def read_pptx(data: bytes, index: int | None) -> Document | list[Document]:
    """Read one slide, or every slide when *index* is None; see :func:`svgwriter.formats.export._office.read_pptx`."""
    presentation_module = require("pptx")
    from ....document import Document

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
        for clicked, spid, effect in read_triggers(slide._element, size):
            sources = drawn.get(clicked, [])
            for element in drawn.get(spid, []) if sources else []:
                _clicked_effect(element, effect, sources[0])
        docs.append(doc)
    return docs if index is None else docs[0]


def _clicked_effect(element: Any, effect: Any, source: Any) -> None:
    """Apply *effect* to *element* so it starts when *source* is clicked (``id.click+delay``)."""
    from ....model.elements.animation import AnimationElement

    before = {id(node) for node in element.iter()}
    apply_effect(element, effect)
    start = f"{source.ensure_id()}.click"
    for node in element.iter():
        if id(node) not in before and isinstance(node, AnimationElement):
            node.set("begin", f"{start}+{effect.begin:g}s" if effect.begin else start)


def _read_shape(parent: Any, shape: Any, drawn: dict[int, list[Any]]) -> None:
    """Add *shape* (recursing into groups) to *parent* as native elements, listed in *drawn* by shape id."""
    from ....model.elements.structure import A, Group, Image, Pixels

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
    if properties is None:
        return None
    style = shape._element.find(f"{{{P_NS}}}style")
    return outline(properties, left, top, width, height, scheme=_scheme(shape), style=style)


def _scheme(shape: Any) -> dict[str, str]:
    """The theme colour scheme of the slide holding *shape* (``accent1``, ``dk1``, ...) as ``#rrggbb``."""
    try:
        master = shape.part.slide.slide_layout.slide_master.part
    except AttributeError:
        return {}
    cached = _SCHEMES.get(id(master))
    if cached is None:
        cached = _SCHEMES[id(master)] = _read_scheme(master)
    return cached


def _read_scheme(master: Any) -> dict[str, str]:
    from lxml import etree

    try:
        theme = etree.fromstring(master.part_related_by(THEME_RELATIONSHIP).blob)
    except (KeyError, ValueError, etree.XMLSyntaxError):
        return {}
    colors = {}
    for entry in theme.iter(_a("clrScheme")):
        for slot in entry:
            value = slot.find(_a("srgbClr"))
            system = slot.find(_a("sysClr"))
            code = value.get("val") if value is not None else system.get("lastClr") if system is not None else None
            if code:
                colors[etree.QName(slot).localname] = "#" + code
        break
    return colors


def outline(properties: Any, left: float, top: float, width: float, height: float, *,
            scheme: dict[str, str] | None = None, style: Any = None) -> Any:
    """The geometry of a DrawingML ``spPr`` as a ``<path>`` with its solid or gradient fill and outline.

    Parameters
    ----------
    properties : lxml element
        The shape properties holding a preset or custom geometry.
    left, top, width, height : float
        The shape's box on the page, in user units.
    scheme : dict of str to str, optional
        Theme colours by slot (``accent1``, ``dk1``, ...) for ``<a:schemeClr>`` fills. Defaults to None.
    style : lxml element, optional
        The shape's ``<p:style>``: its fill and line references paint a shape without its own. Defaults
        to None.

    Returns
    -------
    Path or None
        None when the geometry is unknown or nothing is painted.

    Examples
    --------
    >>> from lxml import etree
    >>> from svgwriter.formats.export._office._pptx_read import outline
    >>> sp = etree.fromstring('<p:spPr xmlns:p="urn:p" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
    ...     '<a:prstGeom prst="rect"/><a:solidFill><a:srgbClr val="FF0000"/></a:solidFill></p:spPr>')
    >>> outline(sp, 0, 0, 10, 5).get("fill").hex
    '#ff0000'
    """
    from ....model.elements.shapes import Path

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
    fill, stroke = _solid(properties.find(_a("solidFill")), scheme), None
    shade = properties.find(_a("gradFill"))
    if fill is None and shade is not None:
        fill = read_gradient(shade, left, top, width, height)
    if fill is None and shade is None and properties.find(_a("noFill")) is None and style is not None:
        fill = _solid(style.find(_a("fillRef")), scheme)
    line = properties.find(_a("ln"))
    if line is None and style is not None:
        stroke = _solid(style.find(_a("lnRef")), scheme)
        if stroke is not None:
            path.set("stroke-width", STYLE_LINE_WIDTH)
    if line is not None and line.find(_a("noFill")) is None:
        stroke = _solid(line.find(_a("solidFill")), scheme)
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


def _solid(fill: Any, scheme: dict[str, str] | None = None) -> Any:
    """The colour of an ``<a:solidFill>`` (or a style reference): an RGB value or a theme slot, alpha included."""
    from ....model.color.color import Color

    if fill is None:
        return None
    rgb, slot = fill.find(_a("srgbClr")), fill.find(_a("schemeClr"))
    if rgb is not None:
        value, source = Color.parse("#" + rgb.get("val")), rgb
    elif slot is not None and scheme:
        code = scheme.get(SCHEME_ALIASES.get(slot.get("val"), slot.get("val")))
        if code is None:
            return None
        value, source = Color.parse(code), slot
    else:
        return None
    value = _modified(value, source)
    alpha = source.find(_a("alpha"))
    return value.with_alpha(int(alpha.get("val")) / ALPHA_SCALE) if alpha is not None else value


def _modified(value: Any, source: Any) -> Any:
    """*value* with DrawingML's colour changes applied in order: ``lumMod``/``lumOff`` (lighter, darker),
    ``tint`` (towards white) and ``shade`` (towards black)."""
    from ....model.color.color import Color

    red, green, blue = value.r, value.g, value.b
    for change in source:
        name, amount = _local_name(change), int(change.get("val", ALPHA_SCALE)) / ALPHA_SCALE
        if name in ("lumMod", "lumOff"):
            hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
            lightness = min(max(lightness * amount if name == "lumMod" else lightness + amount, 0.0), 1.0)
            red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
        elif name == "tint":
            red, green, blue = (channel + (1 - channel) * (1 - amount) for channel in (red, green, blue))
        elif name == "shade":
            red, green, blue = (channel * amount for channel in (red, green, blue))
    if (red, green, blue) == (value.r, value.g, value.b):
        return value
    return Color(red, green, blue, value.a)


def _local_name(node: Any) -> str:
    """The local name of an XML element (``lumMod`` for ``{ns}lumMod``)."""
    tag = node.tag if isinstance(node.tag, str) else ""
    return tag.rsplit("}", 1)[-1]


def _custom_path(geometry: Any, left: float, top: float, width: float, height: float) -> Any:
    """The ``<a:path>`` commands mapped from their own ``w``/``h`` box onto the shape."""
    from ....model.pathdata.builder import PathBuilder

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
    from ....model.elements.shapes import Ellipse, Line, Polygon, Rect

    if name == "rect":
        return Rect(left, top, width, height).local_outline()
    if name == "roundRect":
        radius = min(width, height) * ROUND_RECT_ADJUST / ALPHA_SCALE
        return Rect(left, top, width, height, rx=radius).local_outline()
    if name == "ellipse":
        return Ellipse(left + width / 2, top + height / 2, width / 2, height / 2).local_outline()
    if name in ("line", "straightConnector1"):
        return Line(left, top, left + width, top + height).local_outline()
    points = preset_points(str(name), left, top, width, height)
    if points is None:
        warnings.warn(f"PowerPoint shape {name!r} is not supported yet; drawn as its box", stacklevel=6)
        return Rect(left, top, width, height).local_outline()
    return Polygon(points).local_outline()


def _text(shape: Any, left: float, top: float) -> Any:
    """A text box's paragraphs as one ``<text>`` per line, with font, weight, style and colour, or None."""
    from ....model.elements.structure import Group
    from ....model.elements.text import Text

    if not getattr(shape, "has_text_frame", False) or not (
            shape.text_frame.text.strip() or _math_text(shape.text_frame._txBody)):
        return None
    frame = shape.text_frame
    group = Group()
    if not frame.text.strip():
        return _equation(shape, left, top, group)
    inner_left = left + (frame.margin_left or 0) / EMU_PER_UNIT
    inner_top = top + (frame.margin_top or 0) / EMU_PER_UNIT
    inner_width = (shape.width or 0) / EMU_PER_UNIT - ((frame.margin_left or 0) + (frame.margin_right or 0)) / EMU_PER_UNIT
    inner_height = (shape.height or 0) / EMU_PER_UNIT - ((frame.margin_top or 0) + (frame.margin_bottom or 0)) / EMU_PER_UNIT
    lines = []
    for paragraph in frame.paragraphs:
        font = next((run.font for run in paragraph.runs if run.font.size is not None), None)
        size_units = (font.size.pt if font is not None else DEFAULT_TEXT_PT) / POINTS_PER_UNIT
        lines.append((paragraph, font, size_units))
    total = sum(size * LINE_HEIGHT for _, _, size in lines)
    anchor = frame._txBody.find(_a("bodyPr"))  # noqa: SLF001 - the vertical anchor is not exposed by python-pptx
    vertical = anchor.get("anchor", "t") if anchor is not None else "t"
    line_top = inner_top + max(inner_height - total, 0) * VERTICAL_ANCHORS.get(vertical, 0.0)
    for paragraph, font, size_units in lines:
        content = paragraph.text
        if content:
            properties = paragraph._p.find(_a("pPr"))  # noqa: SLF001 - read the raw alignment code
            align = properties.get("algn", "l") if properties is not None else "l"
            share, text_anchor = HORIZONTAL_ALIGNS.get(align, (0.0, None))
            text = Text(content, x=inner_left + inner_width * share, y=line_top + size_units * ASCENT,
                        font_size=math.floor(size_units * 100) / 100, text_anchor=text_anchor)
            if font is not None:
                _text_style(text, font)
            group.add(text)
        line_top += size_units * LINE_HEIGHT
    return group if len(group) else None


def _equation(shape: Any, left: float, top: float, group: Any) -> Any:
    """An equation box as its characters centred in the box, at the equation's own size."""
    from ....model.elements.text import Text

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
