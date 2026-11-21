"""
Word documents out: the drawing as native Word shapes, pictures, text boxes and equations anchored in one paragraph.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any
from xml.sax.saxutils import escape

from . import require
from ._constants import (
    A_NS,
    ALPHA_SCALE,
    ANGLE_UNIT,
    EMU_PER_UNIT,
    EQUATION_ID,
    HALF_POINTS_PER_UNIT,
    MATH_FONT,
    MC_NS,
    PIC,
    REL,
    TWIPS_PER_UNIT,
    W_NS,
    WP,
    WPS,
)
from ._drawingml import gradient_xml, line_style
from ._pptx import _geometry_xml, _office_family, text_box

if TYPE_CHECKING:
    from ..._internal._flatten import Item
    from ...color.color import Color
    from ...document import Document
    from ._layout import Equation

__all__ = ["write_docx"]

_NAMESPACES = (f'xmlns:w="{W_NS}" xmlns:wp="{WP}" xmlns:a="{A_NS}" xmlns:wps="{WPS}" xmlns:pic="{PIC}" '
               f'xmlns:r="{REL}" xmlns:mc="{MC_NS}"')


def write_docx(document: Document) -> bytes:
    """Write the Word file; see :func:`svgwriter.export._office.docx`."""
    word = require("docx")
    from docx.oxml import parse_xml

    from ..._internal._flatten import flatten
    from ..._internal._layers import pixel_box
    from ._layout import split_equations

    rest, equations = split_equations(document)
    scene = flatten(rest, handled=frozenset({"image"}), text=True)
    out = word.Document()
    drawn = list(scene.painted())
    if not drawn and not scene.texts and equations:
        for equation in equations:
            out.element.body.sectPr.addprevious(parse_xml(f'<w:p xmlns:w="{W_NS}">{_math(equation)}</w:p>'))
    else:
        paragraph = out.add_paragraph()._p
        twips = round(scene.height * TWIPS_PER_UNIT)
        paragraph.append(parse_xml(f'<w:pPr xmlns:w="{W_NS}"><w:spacing w:before="0" w:after="0" '
                                   f'w:line="{twips}" w:lineRule="exact"/></w:pPr>'))
        runs = []
        for item in drawn:
            if isinstance(item, tuple):
                image, matrix = item
                identifier, _ = out.part.get_or_add_image(io.BytesIO(image.encode("png")))
                runs.append(_picture_run(len(runs) + 1, identifier, pixel_box(image, matrix)))
            else:
                runs.extend(_shape_run(len(runs) + 1, item, parse_xml))
        start = len(runs) + 1
        runs.extend(_text_run(start + number, run) for number, run in enumerate(scene.texts))
        runs.extend(_anchor(EQUATION_ID + number, "Equation", equation.x, equation.y, equation.width, equation.height, 0.0,
                            _equation_shape(equation)) for number, equation in enumerate(equations))
        for run in runs:
            paragraph.append(parse_xml(run))
    buffer = io.BytesIO()
    out.save(buffer)
    return buffer.getvalue()


def _anchor(number: int, name: str, x: float, y: float, width: float, height: float, angle: float, shape: str) -> str:
    """A run holding a floating, unwrapped drawing at *x*, *y* (from the paragraph's top left)."""
    left, top = round(x * EMU_PER_UNIT), round(y * EMU_PER_UNIT)
    cx, cy = max(round(width * EMU_PER_UNIT), 1), max(round(height * EMU_PER_UNIT), 1)
    rotation = f' rot="{round(angle * ANGLE_UNIT)}"' if angle else ""
    graphic = shape.replace("{xfrm}", f'<a:xfrm{rotation}><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>')
    uri = PIC if graphic.startswith("<pic:") else WPS
    drawing = (
        f'<w:drawing><wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="{number}" '
        f'behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1"><wp:simplePos x="0" y="0"/>'
        f'<wp:positionH relativeFrom="column"><wp:posOffset>{left}</wp:posOffset></wp:positionH>'
        f'<wp:positionV relativeFrom="paragraph"><wp:posOffset>{top}</wp:posOffset></wp:positionV>'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/>'
        f'<wp:docPr id="{number}" name="{name} {number}"/><wp:cNvGraphicFramePr/>'
        f'<a:graphic><a:graphicData uri="{uri}">{graphic}</a:graphicData></a:graphic></wp:anchor></w:drawing>')
    if uri == WPS:
        drawing = f'<mc:AlternateContent><mc:Choice Requires="wps">{drawing}</mc:Choice></mc:AlternateContent>'
    return f"<w:r {_NAMESPACES}>{drawing}</w:r>"


def _picture_run(number: int, identifier: str, box: Any) -> str:
    """An anchored picture showing the package image *identifier* over *box*."""
    picture = (f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{number}" name="Picture {number}"/><pic:cNvPicPr/>'
               f'</pic:nvPicPr><pic:blipFill><a:blip r:embed="{identifier}"/><a:stretch><a:fillRect/></a:stretch>'
               f'</pic:blipFill><pic:spPr>{{xfrm}}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
               f"</pic:pic>")
    return _anchor(number, "Picture", box.x, box.y, box.width, box.height, 0.0, picture)


def _shape_run(number: int, item: Item, parse_xml: Any) -> list[str]:
    """A flattened item as an anchored custom-geometry Word shape, or nothing when it has no area."""
    from lxml import etree

    from ...ops import from_skia, to_skia

    data = from_skia(to_skia(item.data))
    box = data.bbox
    if box is None:
        return []
    width, height = max(box.width, 1 / EMU_PER_UNIT), max(box.height, 1 / EMU_PER_UNIT)
    geometry = _geometry_xml(data, box.x, box.y, EMU_PER_UNIT, round(width * EMU_PER_UNIT),
                             round(height * EMU_PER_UNIT))
    if item.shading is not None:
        fill = gradient_xml(item.shading, box, item.fill_opacity)
    else:
        fill = _solid_xml(item.fill, item.fill_opacity)
    line = f'<a:ln xmlns:a="{A_NS}"><a:noFill/></a:ln>'
    if item.stroke is not None and item.stroke_width > 0:
        element = parse_xml(f'<a:ln xmlns:a="{A_NS}" w="{round(item.stroke_width * EMU_PER_UNIT)}">'
                            f"{_solid_xml(item.stroke, item.stroke_opacity)}</a:ln>")
        line_style(element, item.stroke_width, item.dashes, item.linecap, item.linejoin, item.miter_limit)
        line = etree.tostring(element, encoding="unicode")
    shape = (f"<wps:wsp><wps:cNvSpPr/><wps:spPr>{{xfrm}}{geometry}{fill}{line}</wps:spPr>"
             f'<wps:bodyPr/></wps:wsp>')
    return [_anchor(number, "Shape", box.x, box.y, width, height, 0.0, shape)]


def _solid_xml(color: Color | None, opacity: float) -> str:
    """``<a:solidFill>`` with alpha, or ``<a:noFill/>``."""
    if color is None or opacity <= 0:
        return f'<a:noFill xmlns:a="{A_NS}"/>'
    red, green, blue, _ = color.uint8
    alpha = f'<a:alpha val="{round(opacity * ALPHA_SCALE)}"/>' if opacity < 1 else ""
    return (f'<a:solidFill xmlns:a="{A_NS}"><a:srgbClr val="{red:02X}{green:02X}{blue:02X}">{alpha}'
            f"</a:srgbClr></a:solidFill>")


def _text_run(number: int, run: Any) -> str:
    """One text run as an unwrapped, borderless text box whose first baseline sits on the run's baseline."""
    left, top, width, height, angle, size = text_box(run)
    family = escape(_office_family(run.family), {'"': "&quot;"})
    properties = (f'<w:rFonts w:ascii="{family}" w:hAnsi="{family}" w:cs="{family}"/>'
                  f'{"<w:b/>" if run.bold else ""}{"<w:i/>" if run.italic else ""}')
    if run.fill is not None:
        red, green, blue, _ = run.fill.uint8
        properties += f'<w:color w:val="{red:02X}{green:02X}{blue:02X}"/>'
    properties += f'<w:sz w:val="{max(round(size * HALF_POINTS_PER_UNIT), 1)}"/>'
    content = (f'<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="{round(height * TWIPS_PER_UNIT)}" '
               f'w:lineRule="exact"/></w:pPr><w:r><w:rPr>{properties}</w:rPr>'
               f'<w:t xml:space="preserve">{escape(run.text)}</w:t></w:r></w:p>')
    return _anchor(number, "Text", left, top, width, height, angle, _text_shape(content, "t"))


def _text_shape(content: str, anchor: str) -> str:
    """A borderless, unfilled text-box shape holding the paragraphs *content*."""
    return (f'<wps:wsp><wps:cNvSpPr txBox="1"/><wps:spPr>{{xfrm}}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f"<a:noFill/><a:ln><a:noFill/></a:ln></wps:spPr><wps:txbx><w:txbxContent>{content}</w:txbxContent>"
            f'</wps:txbx><wps:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}">'
            f"<a:noAutofit/></wps:bodyPr></wps:wsp>")


def _math(equation: Equation) -> str:
    """The ``<m:oMathPara>`` of *equation* in Cambria Math at its drawn size."""
    from ._omml import latex_to_omml

    size = max(round(equation.size * HALF_POINTS_PER_UNIT), 1)
    properties = (f'<w:rPr xmlns:w="{W_NS}"><w:rFonts w:ascii="{MATH_FONT}" w:hAnsi="{MATH_FONT}"/>'
                  f'<w:sz w:val="{size}"/></w:rPr>')
    return latex_to_omml(equation.source, properties)


def _equation_shape(equation: Equation) -> str:
    """A text box with *equation* centred in it."""
    content = (f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/><w:jc w:val="center"/></w:pPr>'
               f"{_math(equation)}</w:p>")
    return _text_shape(content, "ctr")
