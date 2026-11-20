"""
Word documents in: the pictures and DrawingML shapes of a ``.docx`` as elements.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any

from . import require
from ._constants import EMU_PER_UNIT, INLINE_GAP, MARGIN, REL, WP, WPS
from ._pptx import _a, _custom_path, _preset_path, _solid

if TYPE_CHECKING:
    from ...document import Document


def _wp(tag: str) -> str:
    return f"{{{WP}}}{tag}"


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
    fill = _solid(properties.find(_a("solidFill")))
    path.set("fill", fill if fill is not None else "none")
    line = properties.find(_a("ln"))
    if line is not None and line.find(_a("noFill")) is None:
        stroke = _solid(line.find(_a("solidFill")))
        if stroke is not None:
            path.set("stroke", stroke)
            path.set("stroke-width", int(line.get("w", EMU_PER_UNIT)) / EMU_PER_UNIT)
    return path
