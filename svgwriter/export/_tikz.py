"""
TikZ output from a flattened scene.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from .._internal._numbers import format_number
from ._flatten import Item, flatten, to_cubic

if TYPE_CHECKING:
    from ..color.color import Color
    from ..document import Document

__all__ = ["to_tikz"]

PRECISION: Final = 3
CAPS: Final = {"butt": "butt", "round": "round", "square": "rect"}
JOINS: Final = {"miter": "miter", "round": "round", "bevel": "bevel"}


def _n(value: float) -> str:
    return format_number(value, PRECISION)


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


def to_tikz(document: Document, *, standalone: bool = False) -> str:
    """A ``tikzpicture`` in the document's user units (1 unit = 1 pt, y down as in SVG).

    The document is flattened first, so gradients become solid colours and images are skipped.

    Parameters
    ----------
    document : Document
        The drawing.
    standalone : bool, optional
        Wrap in a compilable ``standalone`` LaTeX document. Defaults to False.

    Returns
    -------
    str
        LaTeX source.

    See Also
    --------
    svgwriter.export._eps.to_eps : Another flattened vector format.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._tikz import to_tikz
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, fill="red")
    >>> "begin{tikzpicture}" in to_tikz(doc)
    True
    """
    scene = flatten(document)
    colors: dict[tuple[int, int, int], str] = {}

    def color(value: Color) -> str:
        key = value.uint8[:3]
        if key not in colors:
            colors[key] = f"svgc{len(colors)}"
        return colors[key]

    body = []
    for item in scene.items:
        if not len(item.data):
            continue
        options = []
        if item.fill is not None:
            options.append(f"fill={color(item.fill)}")
            if item.fill_opacity < 1:
                options.append(f"fill opacity={_n(item.fill_opacity)}")
            if item.evenodd:
                options.append("even odd rule")
        if item.stroke is not None and item.stroke_width > 0:
            options += [f"draw={color(item.stroke)}", f"line width={_n(item.stroke_width)}pt",
                        f"line cap={CAPS.get(item.linecap, 'butt')}", f"line join={JOINS.get(item.linejoin, 'miter')}"]
            if item.stroke_opacity < 1:
                options.append(f"draw opacity={_n(item.stroke_opacity)}")
            if item.dashes:
                pattern = " ".join(f"{'on' if i % 2 == 0 else 'off'} {_n(d)}pt"
                                   for i, d in enumerate(item.dashes * (2 if len(item.dashes) % 2 else 1)))
                options.append(f"dash pattern={pattern}")
        if not options:
            continue
        body.append(f"  \\path[{', '.join(options)}] {_path(item)};")
    definitions = [f"\\definecolor{{{name}}}{{RGB}}{{{r},{g},{b}}}" for (r, g, b), name in colors.items()]
    picture = "\n".join([
        *definitions,
        "\\begin{tikzpicture}[x=1pt, y=-1pt]",
        f"  \\useasboundingbox (0,0) rectangle ({_n(scene.width)},{_n(scene.height)});",
        *body,
        "\\end{tikzpicture}",
    ]) + "\n"
    if not standalone:
        return picture
    return "\\documentclass[tikz]{standalone}\n\\begin{document}\n" + picture + "\\end{document}\n"
