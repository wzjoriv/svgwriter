"""
Word documents in: paragraphs, headings and lists as styled text, pictures and shapes in flow or where anchored.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any

from .._constants import BODY_SIZE, BULLET, HEADING_SIZES, INDENT_PER_LEVEL, LINE_HEIGHT, MARGIN
from .._text import Figure, Line, stack
from . import require
from ._constants import (
    ASCENT,
    EMU_PER_UNIT,
    HALF_POINTS_PER_UNIT,
    HEADING_STYLE_RE,
    HEX_COLOR_RE,
    INLINE_GAP,
    LIST_STYLE,
    M_NS,
    MC_NS,
    NUMBERED_STYLE,
    OFF_VALUES,
    REL,
    TITLE_STYLE,
    W_NS,
    WP,
    WPS,
)
from ._pptx import _a
from ._pptx_read import outline

if TYPE_CHECKING:
    from ....document import Document
    from ....model.elements.core import Element

__all__ = ["read_docx"]


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _wp(tag: str) -> str:
    return f"{{{WP}}}{tag}"


def read_docx(data: bytes) -> Document:
    """Read the text and drawings of a Word document; see :func:`svgwriter.formats.export._office.read_docx`."""
    word = require("docx")
    from ....document import Document

    source = word.Document(io.BytesIO(data))
    reader = _Reader(source.part.related_parts)
    flow: list[Line | Figure] = []
    for node in source.element.body:
        if node.tag == _w("p"):
            flow.extend(reader.paragraph(node))
        elif node.tag == _w("tbl"):
            for paragraph in node.iter(_w("p")):
                flow.extend(reader.paragraph(paragraph))
    doc = Document()
    group = stack(flow, gap=INLINE_GAP)
    if len(group):
        doc.add(group)
    for element in reader.floating:
        doc.add(element)
    return doc.fit(padding=MARGIN)


class _Reader:
    """Turns Word paragraphs into lines and figures, collecting anchored items on the side."""

    def __init__(self, parts: Any) -> None:
        self.parts = parts
        self.floating: list[Element] = []
        self.counters: dict[int, int] = {}

    def paragraph(self, node: Any) -> list[Line | Figure]:
        """The lines and inline figures of one ``<w:p>``."""
        properties = node.find(_w("pPr"))
        style = _value(properties, "pStyle") or ""
        level = _heading_level(style, properties)
        size = HEADING_SIZES[level] if level else BODY_SIZE
        base: dict[str, object] = {"font_size": size, "font_weight": "bold"} if level else {}
        blocks: list[Line | Figure] = []
        marker = "" if level else self._marker(style, properties)
        runs: list[object] = [marker] if marker else []
        sizes: list[float] = []
        indent = _list_level(properties) * INDENT_PER_LEVEL if runs else 0.0

        def flush() -> None:
            blocks.append(Line(tuple(runs), max(sizes, default=size), indent, base))
            runs.clear()
            sizes.clear()

        for run, run_size in self._pieces(node):
            if isinstance(run, Figure):
                if any(str(getattr(r, "text_content", r)).strip() for r in runs):
                    flush()
                runs.clear()
                blocks.append(run)
            elif run is None:
                flush()
            else:
                runs.append(run)
                sizes.append(run_size or size)
        if runs or not blocks:
            flush()
        return blocks

    def _marker(self, style: str, properties: Any) -> str:
        """The bullet or number that starts a list paragraph, or an empty string."""
        numbered = style.startswith(NUMBERED_STYLE)
        listed = numbered or style.startswith(LIST_STYLE) or (
            properties is not None and properties.find(_w("numPr")) is not None)
        level = _list_level(properties)
        for deeper in [key for key in self.counters if key > level]:
            del self.counters[deeper]
        if not listed:
            self.counters.clear()
            return ""
        if not numbered:
            return BULLET
        self.counters[level] = self.counters.get(level, 0) + 1
        return f"{self.counters[level]}. "

    def _pieces(self, node: Any) -> list[tuple[Any, float | None]]:
        """Styled runs, figures and line breaks (None) of a paragraph, in reading order."""
        pieces: list[tuple[Any, float | None]] = []
        for child in node:
            if child.tag == _w("r"):
                pieces.extend(self._run(child))
            elif child.tag in (f"{{{M_NS}}}oMath", f"{{{M_NS}}}oMathPara"):
                text = "".join(t.text or "" for t in child.iter(f"{{{M_NS}}}t"))
                pieces.append((text, None))
            elif child.tag != _w("pPr"):
                for run in child.iter(_w("r")):
                    pieces.extend(self._run(run))
        return pieces

    def _run(self, run: Any) -> list[tuple[Any, float | None]]:
        """One ``<w:r>`` as styled text pieces, breaks and figures."""
        from ....model.elements.text import TSpan

        style, size = _run_style(run.find(_w("rPr")))
        pieces: list[tuple[Any, float | None]] = []
        for child in run:
            text = {_w("t"): child.text or "", _w("tab"): " ", _w("noBreakHyphen"): "-"}.get(child.tag)
            if text is not None:
                pieces.append((TSpan(text, **style) if style else text, size))
            elif child.tag in (_w("br"), _w("cr")):
                pieces.append((None, None))
            elif child.tag in (_w("drawing"), f"{{{MC_NS}}}AlternateContent"):
                drawing = child if child.tag == _w("drawing") else next(child.iter(_w("drawing")), None)
                if drawing is not None:
                    pieces.extend((figure, None) for figure in self._drawing(drawing))
        return pieces

    def _drawing(self, drawing: Any) -> list[Figure]:
        """Inline pictures and shapes as figures; anchored ones go to :attr:`floating`."""
        figures = []
        for holder in drawing:
            width, height = _extent(holder)
            if holder.tag == _wp("anchor"):
                x, y = (_offset(holder, axis) for axis in ("positionH", "positionV"))
                self.floating.extend(_items(holder, self.parts, x, y, width, height))
            elif holder.tag == _wp("inline") and _items(holder, self.parts, 0.0, 0.0, width, height):
                figures.append(Figure(height, lambda top, h=holder, w=width, t=height: _group(
                    _items(h, self.parts, 0.0, top, w, t))))
        return figures


def _group(elements: list[Element]) -> Element:
    from ....model.elements.structure import Group

    return elements[0] if len(elements) == 1 else Group(*elements)


def _value(properties: Any, tag: str) -> str | None:
    found = properties.find(_w(tag)) if properties is not None else None
    return found.get(_w("val")) if found is not None else None


def _heading_level(style: str, properties: Any) -> int:
    """1-6 for a title or heading paragraph, 0 otherwise."""
    if style == TITLE_STYLE:
        return 1
    match = HEADING_STYLE_RE.match(style)
    outline = _value(properties, "outlineLvl")
    level = int(match.group(1)) if match else int(outline) + 1 if outline is not None else 0
    return min(level, max(HEADING_SIZES))


def _list_level(properties: Any) -> int:
    numbering = properties.find(_w("numPr")) if properties is not None else None
    level = _value(numbering, "ilvl") if numbering is not None else None
    return int(level) if level is not None else 0


def _on(properties: Any, tag: str) -> bool:
    found = properties.find(_w(tag))
    return found is not None and found.get(_w("val"), "1") not in OFF_VALUES


def _run_style(properties: Any) -> tuple[dict[str, object], float | None]:
    """A run's bold, italic, underline, strike, size, colour and font as tspan attributes, plus its size."""
    if properties is None:
        return {}, None
    style: dict[str, object] = {}
    if _on(properties, "b"):
        style["font_weight"] = "bold"
    if _on(properties, "i"):
        style["font_style"] = "italic"
    decorations = [name for tag, name in (("u", "underline"), ("strike", "line-through")) if _on(properties, tag)]
    if decorations:
        style["text_decoration"] = " ".join(decorations)
    half_points = _value(properties, "sz")
    size = int(half_points) / HALF_POINTS_PER_UNIT if half_points else None
    if size is not None:
        style["font_size"] = size
    color = _value(properties, "color")
    if color and HEX_COLOR_RE.fullmatch(color):
        style["fill"] = f"#{color.lower()}"
    fonts = properties.find(_w("rFonts"))
    family = fonts.get(_w("ascii")) if fonts is not None else None
    if family:
        style["font_family"] = family
    return style, size


def _extent(holder: Any) -> tuple[float, float]:
    extent = holder.find(_wp("extent"))
    if extent is None:
        return 0.0, 0.0
    return int(extent.get("cx", 0)) / EMU_PER_UNIT, int(extent.get("cy", 0)) / EMU_PER_UNIT


def _offset(anchor: Any, axis: str) -> float:
    position = anchor.find(_wp(axis))
    offset = position.find(_wp("posOffset")) if position is not None else None
    return int(offset.text) / EMU_PER_UNIT if offset is not None and offset.text else 0.0


def _items(holder: Any, parts: Any, x: float, y: float, width: float, height: float) -> list[Element]:
    """The picture, shape and text-box text of one drawing at the given box."""
    found = [_picture(holder, parts, x, y, width, height) or _shape(holder, x, y, width, height)]
    content = next(holder.iter(_w("txbxContent")), None)
    if content is not None:
        reader = _Reader(parts)
        lines = [block for node in content.iter(_w("p")) for block in reader.paragraph(node)]
        text = stack(lines)
        if len(text):
            first = next(block for block in lines if isinstance(block, Line))
            found.append(text.translate(x, y + first.size * (ASCENT - LINE_HEIGHT)))
    return [element for element in found if element is not None]


def _picture(holder: Any, parts: Any, x: float, y: float, width: float, height: float) -> Any:
    """An ``<image>`` for a picture whose bytes are in the package, or None."""
    from ....model.elements.structure import Image, Pixels

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
    """A ``<path>`` for a Word shape (preset or custom geometry) with its fill and outline, or None."""
    properties = next(holder.iter(f"{{{WPS}}}spPr"), None)
    return outline(properties, x, y, width, height) if properties is not None else None
