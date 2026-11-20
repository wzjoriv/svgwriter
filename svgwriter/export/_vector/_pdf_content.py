"""
PDF content beyond paths: images, clipping paths and text, as handlers for the PDF reader.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Final

import numpy as np

from ...transform.matrix import Matrix

if TYPE_CHECKING:
    from ._pdf_read import _Painter

__all__ = ["CONTENT_HANDLERS", "draw_image"]

CHANNEL_MAX: Final = 255.0
COMPONENTS: Final = {"DeviceRGB": 3, "DeviceGray": 1, "DeviceCMYK": 4, "CalRGB": 3, "CalGray": 1}
DEFAULT_TEXT_SIZE: Final = 12.0
MATRIX_TOLERANCE: Final = 1e-4
GAP_TOLERANCE: Final = 0.05
_SUBSET_RE: Final = re.compile(r"^[A-Z]{6}\+")
_STYLE_RE: Final = re.compile(r"[-,]?(Bold|Italic|Oblique|BoldItalic|Regular|Roman|MT|PS)+$", re.I)
_WORD_RE: Final = re.compile(r"(?<=[a-z])(?=[A-Z])")
_HEX_RE: Final = re.compile(r"<([0-9A-Fa-f]+)>")
_BF_CHAR_RE: Final = re.compile(r"beginbfchar(.*?)endbfchar", re.S)
_BF_RANGE_RE: Final = re.compile(r"beginbfrange(.*?)endbfrange", re.S)
_RANGE_RE: Final = re.compile(r"<([0-9A-Fa-f]+)>" + r"\s*<([0-9A-Fa-f]+)>" + r"\s*(<[0-9A-Fa-f]+>|\[[^\]]*\])")


def _filters(info: dict[str, Any]) -> list[str]:
    value = info.get("Filter")
    return [str(v) for v in value] if isinstance(value, list) else [str(value)] if value else []


def _samples(painter: _Painter, stream: Any) -> np.ndarray | None:
    """An image XObject's pixels as straight RGBA floats, or None for unsupported encodings."""
    from ...elements.structure import Pixels
    from ._pdf_read import _resolve

    info = stream.info
    filters = _filters(info)
    if "DCTDecode" in filters or "JPXDecode" in filters:
        try:
            return Pixels.decode(stream.raw).rgba()
        except ValueError:
            return None
    if any(f not in ("FlateDecode",) for f in filters) or int(info.get("BitsPerComponent", 8)) != 8:
        return None
    width, height = int(info.get("Width", 0)), int(info.get("Height", 0))
    space = _resolve(painter.objects, info.get("ColorSpace"))
    name = str(space[0] if isinstance(space, list) else space)
    channels = COMPONENTS.get(name)
    if channels is None or not width or not height:
        return None
    from ._pdf_read import _decode

    data = _decode(stream) if filters else stream.raw
    raw = np.frombuffer(data[:width * height * channels], np.uint8)
    if raw.size < width * height * channels:
        return None
    pixels = raw.reshape(height, width, channels).astype(np.float32) / CHANNEL_MAX
    if channels == 1:
        rgb = np.repeat(pixels, 3, axis=2)
    elif channels == 4:
        c, m, y, k = (pixels[..., i] for i in range(4))
        rgb = np.dstack([(1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k)])
    else:
        rgb = pixels
    alpha = np.ones((height, width, 1), np.float32)
    mask = _resolve(painter.objects, info.get("SMask"))
    if mask is not None and hasattr(mask, "info"):
        soft = _samples(painter, mask)
        if soft is not None and soft.shape[:2] == (height, width):
            alpha = soft[..., :1]
    return np.concatenate([rgb, alpha], axis=2)


def draw_image(painter: _Painter, stream: Any) -> None:
    """``Do`` on an image XObject: an ``<image>`` mapped through the CTM onto the unit square."""
    from ...elements.structure import Image

    pixels = _samples(painter, stream)
    if pixels is None:
        return
    rows, columns = pixels.shape[:2]
    image = Image(pixels, 0, 0, columns, rows, preserve_aspect_ratio="none")
    image.t = painter.state.ctm @ Matrix(1 / columns, 0, 0, -1 / rows, 0, 1)
    if painter.state.clip:
        _clip(image, painter.state.clip)
    painter.shapes.append(image)


def _clip(element: Any, ops: list[Any]) -> None:
    """Clip *element* (in page space) to the outline *ops*, given in page space too."""
    from ._reading import Shape, _path

    outline = _path(Shape(ops))
    outline.t = element.t.inverse() if element.t is not None else outline.t
    element.clip(outline)


def _set_clip(painter: _Painter, evenodd: bool) -> None:
    """``W``/``W*``: the current path becomes the clip once it is painted (or discarded with ``n``)."""
    painter.pending_clip = evenodd


def _text_begin(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    painter.text_matrix = painter.line_matrix = Matrix()


def _font(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    """``Tf``: font resource and size; the family comes from the font's base name."""
    from ._pdf_read import _numbers

    font = painter.resource(resources, "Font", operands[0]) or {}
    font = font if isinstance(font, dict) else {}
    base = _SUBSET_RE.sub("", str(font.get("BaseFont", "")).lstrip("/"))
    style = base.lower()
    painter.text_font = (_family(_STYLE_RE.sub("", base)), "bold" in style, "italic" in style or "oblique" in style)
    painter.text_size = _numbers(operands[1:], 1)[0]
    painter.text_codes = (2 if str(font.get("Subtype", "")).lstrip("/") == "Type0" else 1,
                          _to_unicode(painter, font.get("ToUnicode")))


def _family(name: str) -> str:
    """A font family from a PostScript base name: as written when installed, else split into words."""
    import skia

    if not name:
        return "serif"
    spaced = _WORD_RE.sub(" ", name)
    for candidate in dict.fromkeys((name, spaced)):
        if skia.Typeface(candidate).getFamilyName().lower() == candidate.lower():
            return candidate
    return name


def _to_unicode(painter: _Painter, value: Any) -> dict[int, str]:
    """The character codes of a ``/ToUnicode`` CMap mapped to their text (empty when there is none)."""
    from ._pdf_read import _decode, _resolve

    stream = _resolve(painter.objects, value)
    if stream is None or not hasattr(stream, "info"):
        return {}
    cmap = _decode(stream).decode("latin-1") if stream.info.get("Filter") else stream.raw.decode("latin-1")
    table: dict[int, str] = {}
    for block in _BF_CHAR_RE.findall(cmap):
        codes = _HEX_RE.findall(block)
        for code, text in zip(codes[::2], codes[1::2], strict=False):
            table[int(code, 16)] = _utf16(text)
    for block in _BF_RANGE_RE.findall(cmap):
        for low, high, target in _RANGE_RE.findall(block):
            first, last = int(low, 16), int(high, 16)
            if target.startswith("["):
                for offset, text in enumerate(_HEX_RE.findall(target)):
                    table[first + offset] = _utf16(text)
            else:
                start = int(target[1:-1], 16)
                width = len(target) - 2
                for offset in range(last - first + 1):
                    table[first + offset] = _utf16(format(start + offset, f"0{width}X"))
    return table


def _utf16(hex_text: str) -> str:
    return bytes.fromhex(hex_text).decode("utf-16-be", errors="replace")


def _move(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    from ._pdf_read import _numbers

    tx, ty = _numbers(operands, 2)
    painter.line_matrix = painter.line_matrix @ Matrix.translate(tx, ty)
    painter.text_matrix = painter.line_matrix


def _set_matrix(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    from ._pdf_read import _numbers

    painter.text_matrix = painter.line_matrix = Matrix(*_numbers(operands, 6))


def _next_line(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    painter.line_matrix = painter.line_matrix @ Matrix.translate(0, -painter.leading)
    painter.text_matrix = painter.line_matrix


def _show(painter: _Painter, text: str) -> None:
    """Add a ``<text>`` run at the current text position and advance by its measured width."""
    from ...elements.text import Text
    from ...ops.text import text_width
    from ._reading import _hex

    if not text.strip():
        return
    family, bold, italic = getattr(painter, "text_font", ("serif", False, False))
    size = getattr(painter, "text_size", DEFAULT_TEXT_SIZE) or DEFAULT_TEXT_SIZE
    style = (family, bold, italic, size, painter.state.fill, painter.state.fill_alpha * painter.state.group_alpha,
             id(painter.state.clip))
    if _continue_run(painter, text, style, size):
        return
    run = Text(text, x=0, y=0, font_size=size, font_family=family, fill=_hex(painter.state.fill),
               font_weight="bold" if bold else None, font_style="italic" if italic else None,
               xml_space="preserve")
    if painter.state.fill_alpha * painter.state.group_alpha < 1:
        run.set("fill-opacity", painter.state.fill_alpha * painter.state.group_alpha)
    run.t = painter.state.ctm @ painter.text_matrix @ Matrix.scale(1, -1)
    if painter.state.clip:
        _clip(run, painter.state.clip)
    painter.shapes.append(run)
    width = text_width(text, family, size, weight="bold" if bold else "normal", italic=italic)
    painter.text_matrix = painter.text_matrix @ Matrix.translate(width, 0)
    painter.last_text = (painter.shapes[-1], run, style, painter.state.ctm @ painter.text_matrix)


def _continue_run(painter: _Painter, text: str, style: tuple[Any, ...], size: float) -> bool:
    """Append *text* to the previous run when it starts where that run ends (or one space later).

    PDF writers often place every glyph on its own; joining them keeps words as one ``<text>``.
    """
    from ...ops.text import text_width

    last = getattr(painter, "last_text", None)
    if last is None or not painter.shapes or painter.shapes[-1] is not last[0] or last[2] != style:
        return False
    start = painter.state.ctm @ painter.text_matrix
    try:
        step = last[3].inverse() @ start
    except ValueError:
        return False
    if (abs(step.a - 1) > MATRIX_TOLERANCE or abs(step.d - 1) > MATRIX_TOLERANCE or abs(step.b) > MATRIX_TOLERANCE
            or abs(step.c) > MATRIX_TOLERANCE or abs(step.f) > size * GAP_TOLERANCE):
        return False
    family, bold, italic = style[:3]
    weight = "bold" if bold else "normal"
    space = text_width(" ", family, size, weight=weight, italic=italic)
    if abs(step.e) <= size * GAP_TOLERANCE:
        joined = text
    elif abs(step.e - space) <= size * GAP_TOLERANCE:
        joined = " " + text
    else:
        return False
    run = last[1]
    run.text_content = run.text_content + joined
    width = text_width(text, family, size, weight=weight, italic=italic)
    painter.text_matrix = painter.text_matrix @ Matrix.translate(width, 0)
    painter.last_text = (last[0], run, style, painter.state.ctm @ painter.text_matrix)
    return True


def _string(painter: _Painter, value: Any) -> str:
    """A shown string as text: codes looked up in the font's ``/ToUnicode`` map, else read as Latin-1."""
    if not isinstance(value, bytes | bytearray):
        return str(value)
    width, table = getattr(painter, "text_codes", (1, {}))
    if not table:
        return value.decode("latin-1")
    codes = [int.from_bytes(value[i:i + width], "big") for i in range(0, len(value) - width + 1, width)]
    return "".join(table.get(code, chr(code) if width == 1 else "") for code in codes)


def _show_text(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    _show(painter, _string(painter, operands[-1]))


def _show_array(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    """``TJ``: strings with kerning adjustments (thousandths of an em), shown as one run."""
    parts = operands[-1] if isinstance(operands[-1], list) else []
    _show(painter, "".join(_string(painter, p) for p in parts if not isinstance(p, int | float)))


def _quote(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    _next_line(painter, [], resources)
    _show(painter, _string(painter, operands[-1]))


def _leading(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    from ._pdf_read import _numbers

    painter.leading = _numbers(operands, 1)[0]


def _move_leading(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    from ._pdf_read import _numbers

    painter.leading = -_numbers(operands, 2)[1]
    _move(painter, operands, resources)


CONTENT_HANDLERS: Final = {
    "W": lambda p, o, r: _set_clip(p, False),
    "W*": lambda p, o, r: _set_clip(p, True),
    "BT": _text_begin,
    "Tf": _font,
    "Td": _move,
    "TD": _move_leading,
    "Tm": _set_matrix,
    "T*": _next_line,
    "TL": _leading,
    "Tj": _show_text,
    "TJ": _show_array,
    "'": _quote,
    '"': _quote,
}
