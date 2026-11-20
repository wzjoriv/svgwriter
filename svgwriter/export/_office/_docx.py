"""
Word documents: the drawing as a picture with editable equations out, pictures and DrawingML shapes in.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any

from . import _picture as _drawing
from . import require
from ._constants import (
    A_NS,
    EMU_PER_UNIT,
    EQUATION_ID,
    HALF_POINTS_PER_UNIT,
    INLINE_GAP,
    MARGIN,
    MATH_FONT,
    REL,
    W_NS,
    WP,
    WPS,
)
from ._pptx import _a, _custom_path, _preset_path, _solid

if TYPE_CHECKING:
    from ...document import Document
    from ._layout import Equation


def _wp(tag: str) -> str:
    return f"{{{WP}}}{tag}"


def write_docx(document: Document) -> bytes:
    """Write the Word file; see :func:`svgwriter.export._office.docx`."""
    word = require("docx")
    shared = require("docx.shared")
    from docx.oxml import parse_xml

    from ._layout import split_equations

    rest, equations = split_equations(document)
    out = word.Document()
    if not equations or rest.content_bounds() is not None:
        png, width, height = _drawing(rest)
        out.add_picture(io.BytesIO(png), width=shared.Inches(width), height=shared.Inches(height))
        paragraph = out.paragraphs[-1]._p
        for number, equation in enumerate(equations):
            paragraph.append(parse_xml(_floating(equation, EQUATION_ID + number)))
    else:
        for equation in equations:
            out.element.body.sectPr.addprevious(parse_xml(f'<w:p xmlns:w="{W_NS}">{_math(equation)}</w:p>'))
    buffer = io.BytesIO()
    out.save(buffer)
    return buffer.getvalue()


def _math(equation: Equation) -> str:
    """The ``<m:oMathPara>`` of *equation* in Cambria Math at its drawn size."""
    from ._omml import latex_to_omml

    size = max(round(equation.size * HALF_POINTS_PER_UNIT), 1)
    properties = (f'<w:rPr xmlns:w="{W_NS}"><w:rFonts w:ascii="{MATH_FONT}" w:hAnsi="{MATH_FONT}"/>'
                  f'<w:sz w:val="{size}"/></w:rPr>')
    return latex_to_omml(equation.source, properties)


def _floating(equation: Equation, number: int) -> str:
    """A run holding a borderless text box with *equation*, floating over the picture at the group's place."""
    x, y = round(equation.x * EMU_PER_UNIT), round(equation.y * EMU_PER_UNIT)
    width, height = round(equation.width * EMU_PER_UNIT), round(equation.height * EMU_PER_UNIT)
    return (
        f'<w:r xmlns:w="{W_NS}" xmlns:wp="{WP}" xmlns:a="{A_NS}" xmlns:wps="{WPS}" '
        f'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
        f'<mc:AlternateContent><mc:Choice Requires="wps"><w:drawing>'
        f'<wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="{number}" behindDoc="0" '
        f'locked="0" layoutInCell="1" allowOverlap="1"><wp:simplePos x="0" y="0"/>'
        f'<wp:positionH relativeFrom="column"><wp:posOffset>{x}</wp:posOffset></wp:positionH>'
        f'<wp:positionV relativeFrom="paragraph"><wp:posOffset>{y}</wp:posOffset></wp:positionV>'
        f'<wp:extent cx="{width}" cy="{height}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/>'
        f'<wp:docPr id="{number}" name="Equation {number}"/><wp:cNvGraphicFramePr/>'
        f'<a:graphic><a:graphicData uri="{WPS}"><wps:wsp><wps:cNvSpPr txBox="1"/><wps:spPr>'
        f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{width}" cy="{height}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></wps:spPr>'
        f'<wps:txbx><w:txbxContent><w:p><w:pPr><w:spacing w:before="0" w:after="0"/><w:jc w:val="center"/>'
        f"</w:pPr>{_math(equation)}</w:p></w:txbxContent></wps:txbx>"
        f'<wps:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:noAutofit/></wps:bodyPr>'
        f"</wps:wsp></a:graphicData></a:graphic></wp:anchor></w:drawing></mc:Choice></mc:AlternateContent></w:r>")


def read_docx(data: bytes) -> Document:
    """Read the drawings of a Word document; see :func:`svgwriter.export._office.read_docx`."""
    word = require("docx")
    from ...document import Document

    source = word.Document(io.BytesIO(data))
    parts = source.part.related_parts
    doc = Document()
    cursor = 0.0
    for holder in source.element.body.iter(_wp("inline"), _wp("anchor")):
        extent = holder.find(_wp("extent"))
        width = int(extent.get("cx", 0)) / EMU_PER_UNIT if extent is not None else 0.0
        height = int(extent.get("cy", 0)) / EMU_PER_UNIT if extent is not None else 0.0
        if holder.tag == _wp("anchor"):
            x, y = (_offset(holder, axis) for axis in ("positionH", "positionV"))
        else:
            x, y = 0.0, cursor
            cursor += height + INLINE_GAP
        element = _picture(holder, parts, x, y, width, height) or _shape(holder, x, y, width, height)
        if element is not None:
            doc.add(element)
    return doc.fit(padding=MARGIN)


def _offset(anchor: Any, axis: str) -> float:
    position = anchor.find(_wp(axis))
    offset = position.find(_wp("posOffset")) if position is not None else None
    return int(offset.text) / EMU_PER_UNIT if offset is not None and offset.text else 0.0


def _picture(holder: Any, parts: Any, x: float, y: float, width: float, height: float) -> Any:
    """An ``<image>`` for a picture whose bytes are in the package, or None."""
    from ...elements.structure import Image, Pixels

    blip = next(holder.iter(_a("blip")), None)
    target = blip.get(f"{{{REL}}}embed") if blip is not None else None
    if target is None or target not in parts:
        return None
    try:
        pixels = Pixels.decode(parts[target].blob)
    except ValueError:
        return None
    return Image(pixels.rgba(), x, y, width, height, preserve_aspect_ratio="none")


def _shape(holder: Any, x: float, y: float, width: float, height: float) -> Any:
    """A ``<path>`` for a Word shape (preset or custom geometry) with its solid fill and outline, or None."""
    from ...elements.shapes import Path

    properties = next(holder.iter(f"{{{WPS}}}spPr"), None)
    if properties is None:
        return None
    custom, preset = properties.find(_a("custGeom")), properties.find(_a("prstGeom"))
    data = (_custom_path(custom, x, y, width, height) if custom is not None
            else _preset_path(preset.get("prst"), x, y, width, height) if preset is not None else None)
    if data is None:
        return None
    path = Path(data)
    fill, stroke = _solid(properties.find(_a("solidFill"))), None
    path.set("fill", fill if fill is not None else "none")
    line = properties.find(_a("ln"))
    if line is not None and line.find(_a("noFill")) is None:
        stroke = _solid(line.find(_a("solidFill")))
        if stroke is not None:
            path.set("stroke", stroke)
            path.set("stroke-width", int(line.get("w", EMU_PER_UNIT)) / EMU_PER_UNIT)
    return path if fill is not None or stroke is not None else None
