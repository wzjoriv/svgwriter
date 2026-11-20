"""
Encapsulated PostScript output from a flattened scene.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal._numbers import format_number
from ...transform.matrix import Matrix
from .._flatten import Item, flatten, to_cubic
from .._paints import Shading
from .._patterns import placed_images
from ._constants import (
    AXIAL,
    BASE_LEVEL,
    EPS_CAPS,
    EPS_CHANNEL_MAX,
    EPS_JOINS,
    EPS_PRECISION,
    HEX_LINE,
    LEVEL_LINE,
    MONOSPACE_WORDS,
    POSTSCRIPT_FONTS,
    PS_ESCAPES,
    RADIAL,
    SERIF_WORDS,
    SHADING_LEVEL,
)

if TYPE_CHECKING:
    from ...color.color import Color
    from ...document import Document

__all__ = ["to_eps"]


def _n(value: float) -> str:
    return format_number(value, EPS_PRECISION)


def _path(item: Item, height: float) -> str:
    parts = ["newpath"]
    for op, args in to_cubic(item.data):
        flipped = [v if i % 2 == 0 else height - v for i, v in enumerate(args)]
        coords = " ".join(_n(v) for v in flipped)
        parts.append({"M": f"{coords} moveto", "L": f"{coords} lineto", "C": f"{coords} curveto",
                      "Z": "closepath"}[op])
    return "\n".join(parts)


def _image(image: Any, matrix: Matrix, height: float) -> str:
    """An embedded image as ``colorimage`` in its pixel grid; alpha is composited onto white (EPS has none)."""
    rgba = image.rgba()
    rgb = rgba[..., :3] * rgba[..., 3:] + (1.0 - rgba[..., 3:])
    data = np.clip(np.rint(rgb * EPS_CHANNEL_MAX), 0, EPS_CHANNEL_MAX).astype(np.uint8).tobytes().hex()
    rows, columns = rgba.shape[:2]
    flip = Matrix(1, 0, 0, -1, 0, height) @ matrix
    lines = [data[i:i + HEX_LINE] for i in range(0, len(data), HEX_LINE)]
    return "\n".join([
        "gsave", f"[{' '.join(_n(v) for v in flip.as_tuple())}] concat",
        f"{columns} {rows} 8 [1 0 0 1 0 0] currentfile /ASCIIHexDecode filter false 3 colorimage",
        *lines, ">", "grestore",
    ])


def _rgb(color: Color) -> str:
    return " ".join(_n(v) for v in color.rgb)


def _function(stops: list[tuple[float, Color]]) -> str:
    """A PostScript color function through the stops (exponential pieces stitched together)."""
    points = list(stops)
    if points[0][0] > 0:
        points.insert(0, (0.0, points[0][1]))
    if points[-1][0] < 1:
        points.append((1.0, points[-1][1]))
    pieces = [f"<< /FunctionType 2 /Domain [0 1] /C0 [{_rgb(a)}] /C1 [{_rgb(b)}] /N 1 >>"
              for (_, a), (_, b) in zip(points, points[1:], strict=False)]
    if len(pieces) == 1:
        return pieces[0]
    bounds = " ".join(_n(offset) for offset, _ in points[1:-1])
    encode = " ".join("0 1" for _ in pieces)
    return (f"<< /FunctionType 3 /Domain [0 1] /Functions [{' '.join(pieces)}] /Bounds [{bounds}] "
            f"/Encode [{encode}] >>")


def _shfill(shading: Shading, height: float) -> str:
    """``concat`` into gradient space, then an axial or radial ``shfill`` (PostScript level 3)."""
    flip = Matrix(1, 0, 0, -1, 0, height) @ shading.matrix
    kind = AXIAL if shading.kind == "axial" else RADIAL
    coords = " ".join(_n(v) for v in shading.coords)
    return (f"[{' '.join(_n(v) for v in flip.as_tuple())}] concat\n"
            f"<< /ShadingType {kind} /ColorSpace /DeviceRGB /Coords [{coords}] /Extend [true true] "
            f"/Function {_function(shading.stops)} >> shfill")


def _postscript_font(run: Any) -> str:
    names = run.family.lower()
    kind = "mono" if any(w in names for w in MONOSPACE_WORDS) else (
        "serif" if any(w in names for w in SERIF_WORDS) or ("serif" in names and "sans" not in names) else "sans")
    return POSTSCRIPT_FONTS[(kind, run.bold, run.italic)]


def _text(run: Any, height: float) -> str:
    """A text run as PostScript ``show`` in a standard font, or its glyph outlines when it is not ASCII."""
    from ...ops.text import text_outline

    flip = Matrix(1, 0, 0, -1, 0, height)
    color = run.fill.rgb if run.fill is not None else (0.0, 0.0, 0.0)
    paint = f"{_n(color[0])} {_n(color[1])} {_n(color[2])} setrgbcolor"
    if run.text.isascii():
        frame = flip @ run.matrix @ Matrix.scale(1, -1)
        escaped = "".join(PS_ESCAPES.get(char, char) for char in run.text)
        return "\n".join([
            "gsave", f"[{' '.join(_n(v) for v in frame.as_tuple())}] concat", paint,
            f"/{_postscript_font(run)} findfont {_n(run.size)} scalefont setfont",
            f"0 0 moveto ({escaped}) show", "grestore",
        ])
    outline = text_outline(run.text, run.family, run.size, weight="bold" if run.bold else "normal",
                           italic=run.italic).transformed(run.matrix)
    item = Item(outline, run.fill, 1.0, False, None, 1.0, 0.0, "butt", "miter", 4.0, ())
    return "\n".join([_path(item, height), paint, "fill"])


def to_eps(document: Document, *, text: bool = True) -> str:
    """EPS (PostScript level 2) in points, one user unit per point.

    The document is flattened first, so gradients become solid colours and images are skipped.

    Parameters
    ----------
    document : Document
        The document to convert.

    Returns
    -------
    str
        PostScript source.

    See Also
    --------
    svgwriter.export._vector._tikz.to_tikz : Another flattened vector format.

    Notes
    -----
    PostScript has no transparency; translucent paints are written opaque.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._vector._eps import to_eps
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> to_eps(doc).splitlines()[:2]
    ['%!PS-Adobe-3.0 EPSF-3.0', '%%BoundingBox: 0 0 10 10']
    """
    scene = flatten(document, handled=frozenset({"image"}), text=text)
    level = BASE_LEVEL
    lines = [
        "%!PS-Adobe-3.0 EPSF-3.0",
        f"%%BoundingBox: 0 0 {math.ceil(scene.width)} {math.ceil(scene.height)}",
        f"%%HiResBoundingBox: 0 0 {_n(scene.width)} {_n(scene.height)}",
        "%%Creator: svgwriter",
        "%%LanguageLevel: {level}",
        "%%EndComments",
        "gsave",
    ]
    for image, matrix in placed_images(document):
        lines.append(_image(image, matrix, scene.height))
    for item in scene.items:
        if not len(item.data):
            continue
        path = _path(item, scene.height)
        if item.shading is not None:
            level = SHADING_LEVEL
            lines += ["gsave", path, "eoclip" if item.evenodd else "clip", _shfill(item.shading, scene.height),
                      "grestore"]
        elif item.fill is not None:
            r, g, b = item.fill.rgb
            lines += [path, f"{_n(r)} {_n(g)} {_n(b)} setrgbcolor", "eofill" if item.evenodd else "fill"]
        if item.stroke is not None and item.stroke_width > 0:
            r, g, b = item.stroke.rgb
            dashes = " ".join(_n(d) for d in item.dashes)
            lines += [path, f"{_n(r)} {_n(g)} {_n(b)} setrgbcolor", f"{_n(item.stroke_width)} setlinewidth",
                      f"{EPS_CAPS.get(item.linecap, 0)} setlinecap {EPS_JOINS.get(item.linejoin, 0)} setlinejoin",
                      f"{_n(item.miter_limit)} setmiterlimit [{dashes}] 0 setdash", "stroke"]
    lines += [_text(run, scene.height) for run in scene.texts]
    lines += ["grestore", "showpage", "%%EOF"]
    lines[LEVEL_LINE] = f"%%LanguageLevel: {level}"
    return "\n".join(lines) + "\n"
