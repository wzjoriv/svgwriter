"""
TikZ output from a flattened scene.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..._internal._constants import PX_PER_INCH
from ..._internal._flatten import Item, flatten, to_cubic
from ..._internal._numbers import format_number
from ..._internal._paints import Shading
from ..._internal._typography._emoji import color_glyph_cells
from ._constants import (
    ANGLE_EPSILON,
    LATEX_SPECIALS,
    LINE_SPREAD,
    MONOSPACE_WORDS,
    PX_PER_BP,
    PX_PER_TEX_PT,
    SERIF_WORDS,
    TIKZ_CAPS,
    TIKZ_EMOJI_PIXELS,
    TIKZ_JOINS,
    TIKZ_PRECISION,
    TIKZ_STANDALONE,
)
from ._units import unit_scale

if TYPE_CHECKING:
    from ...color.color import Color
    from ...document import Document

__all__ = ["to_tikz"]


def _n(value: float) -> str:
    return format_number(value, TIKZ_PRECISION)


def _path(item: Item) -> str:
    parts = []
    for op, args in to_cubic(item.data):
        if op == "M":
            parts.append(f"({_n(args[0])},{_n(args[1])})")
        elif op == "L":
            parts.append(f"-- ({_n(args[0])},{_n(args[1])})")
        elif op == "C":
            parts.append(f".. controls ({_n(args[0])},{_n(args[1])}) and ({_n(args[2])},{_n(args[3])}) "
                         f".. ({_n(args[4])},{_n(args[5])})")
        else:
            parts.append("-- cycle")
    return " ".join(parts)


def _escape(text: str) -> str:
    return "".join(LATEX_SPECIALS.get(char, char) for char in text)


def _family(family: str) -> str:
    """The LaTeX family switch for a CSS family list: monospace, serif, else sans-serif."""
    names = family.lower()
    if any(word in names for word in MONOSPACE_WORDS):
        return r"\ttfamily"
    if any(word in names for word in SERIF_WORDS) or ("serif" in names and "sans" not in names):
        return r"\rmfamily"
    return r"\sffamily"


def _node(run: Any, color: Callable[[Color], str], tex_pt: float) -> str:
    """A text run as a ``\\node`` anchored at its baseline start, sized, coloured and turned like the SVG."""
    matrix = run.matrix
    size = run.size * math.sqrt(abs(matrix.determinant)) / tex_pt
    angle = math.degrees(math.atan2(matrix.b, matrix.a))
    font = f"\\fontsize{{{_n(size)}}}{{{_n(size * LINE_SPREAD)}}}\\selectfont"
    font += _family(run.family)
    font += "\\bfseries" if run.bold else ""
    font += "\\itshape" if run.italic else ""
    options = ["anchor=base west", "inner sep=0pt", "outer sep=0pt", f"font={font}"]
    if run.fill is not None:
        options.append(f"text={color(run.fill)}")
    if run.opacity < 1:
        options.append(f"text opacity={_n(run.opacity)}")
    if abs(angle) > ANGLE_EPSILON:
        options.append(f"rotate={_n(-angle)}")
    return f"  \\node[{', '.join(options)}] at ({_n(matrix.e)},{_n(matrix.f)}) {{{_escape(run.text)}}};"


def _shading_options(shading: Shading, color: Callable[[Color], str]) -> list[str]:
    """TikZ shading keys for a gradient: axis shading at the gradient's angle, or radial; stretched over the shape."""
    first, last = shading.stops[0][1], shading.stops[-1][1]
    if shading.kind == "radial":
        return ["shading=radial", f"inner color={color(first)}", f"outer color={color(last)}"]
    x1, y1, x2, y2 = shading.coords
    start, end = shading.matrix.apply(x1, y1), shading.matrix.apply(x2, y2)
    dx, dy = end.x - start.x, -(end.y - start.y)
    angle = math.degrees(math.atan2(dx, -dy))
    keys = ["shading=axis", f"top color={color(first)}", f"bottom color={color(last)}"]
    if len(shading.stops) > 2:
        keys.append(f"middle color={color(shading.stops[len(shading.stops) // 2][1])}")
    return [*keys, f"shading angle={_n(angle)}"]


def to_tikz(document: Document, *, standalone: bool = False, text: bool = True,
            px_per_inch: float = PX_PER_INCH) -> str:
    """A ``tikzpicture`` at the document's physical size: 1 user unit = 0.75 bp (96 per inch), y down as in SVG.

    The document is flattened first: gradients become TikZ shadings and images are skipped. Text is
    written as ``\\node`` commands typeset by LaTeX (``text=False`` writes glyph outlines instead).
    LaTeX cannot typeset colour emoji, so they are drawn as small filled pixel cells.

    Parameters
    ----------
    document : Document
        The drawing.
    standalone : bool, optional
        Wrap in a compilable ``standalone`` LaTeX document. Defaults to False.
    text : bool, optional
        Keep text as LaTeX text; False draws the exact glyph outlines. Defaults to True.
    px_per_inch : float, optional
        User units per inch of a document sized in pixels; 72 draws one unit as one point.
        Sizes in ``mm``, ``cm``, ``in``, ``pt`` or ``pc`` are kept. Defaults to 96.

    Returns
    -------
    str
        LaTeX source.

    See Also
    --------
    svgwriter.export._vector._eps.to_eps : Another flattened vector format.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._vector._tikz import to_tikz
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> "begin{tikzpicture}" in to_tikz(doc)
    True
    """
    scene = flatten(document, text=text, color_glyphs=False)
    scale = unit_scale(document, px_per_inch)
    bp, tex_pt = PX_PER_BP / scale, PX_PER_TEX_PT / scale
    colors: dict[tuple[int, int, int], str] = {}

    def color(value: Color) -> str:
        key = value.uint8[:3]
        if key not in colors:
            colors[key] = f"svgc{len(colors)}"
        return colors[key]

    body = []
    for item in [*scene.items, *color_glyph_cells(document, TIKZ_EMOJI_PIXELS)]:
        if not len(item.data):
            continue
        options = []
        if item.shading is not None:
            options += _shading_options(item.shading, color)
            if item.fill_opacity < 1:
                options.append(f"fill opacity={_n(item.fill_opacity)}")
        elif item.fill is not None:
            options.append(f"fill={color(item.fill)}")
            if item.fill_opacity < 1:
                options.append(f"fill opacity={_n(item.fill_opacity)}")
            if item.evenodd:
                options.append("even odd rule")
        if item.stroke is not None and item.stroke_width > 0:
            options += [f"draw={color(item.stroke)}", f"line width={_n(item.stroke_width / bp)}bp",
                        f"line cap={TIKZ_CAPS.get(item.linecap, 'butt')}", f"line join={TIKZ_JOINS.get(item.linejoin, 'miter')}"]
            if item.stroke_opacity < 1:
                options.append(f"draw opacity={_n(item.stroke_opacity)}")
            if item.dashes:
                pattern = " ".join(f"{'on' if i % 2 == 0 else 'off'} {_n(d / bp)}bp"
                                   for i, d in enumerate(item.dashes * (2 if len(item.dashes) % 2 else 1)))
                options.append(f"dash pattern={pattern}")
        if not options:
            continue
        body.append(f"  \\path[{', '.join(options)}] {_path(item)};")
    body += [_node(run, color, tex_pt) for run in scene.texts]
    definitions = [f"\\definecolor{{{name}}}{{RGB}}{{{r},{g},{b}}}" for (r, g, b), name in colors.items()]
    picture = "\n".join([
        *definitions,
        f"\\begin{{tikzpicture}}[x={_n(1 / bp)}bp, y={_n(-1 / bp)}bp]",
        f"  \\useasboundingbox (0,0) rectangle ({_n(scene.width)},{_n(scene.height)});",
        *body,
        "\\end{tikzpicture}",
    ]) + "\n"
    if not standalone:
        return picture
    return TIKZ_STANDALONE + "\\begin{document}\n" + picture + "\\end{document}\n"
