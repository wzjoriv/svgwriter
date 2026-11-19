"""Encapsulated PostScript output from a flattened scene."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Final

from .._internal._numbers import format_number
from ._flatten import Item, flatten, to_cubic

if TYPE_CHECKING:
    from ..document import Document

__all__ = ["to_eps"]

PRECISION: Final = 3
CAPS: Final = {"butt": 0, "round": 1, "square": 2}
JOINS: Final = {"miter": 0, "round": 1, "bevel": 2}


def _n(value: float) -> str:
    return format_number(value, PRECISION)


def _path(item: Item, height: float) -> str:
    parts = ["newpath"]
    for op, args in to_cubic(item.data):
        flipped = [v if i % 2 == 0 else height - v for i, v in enumerate(args)]
        coords = " ".join(_n(v) for v in flipped)
        parts.append({"M": f"{coords} moveto", "L": f"{coords} lineto", "C": f"{coords} curveto",
                      "Z": "closepath"}[op])
    return "\n".join(parts)


def to_eps(document: Document) -> str:
    """EPS (PostScript level 2) in points, one user unit per point.

    Notes
    -----
    PostScript has no transparency; translucent paints are written opaque.
    """
    scene = flatten(document)
    lines = [
        "%!PS-Adobe-3.0 EPSF-3.0",
        f"%%BoundingBox: 0 0 {math.ceil(scene.width)} {math.ceil(scene.height)}",
        f"%%HiResBoundingBox: 0 0 {_n(scene.width)} {_n(scene.height)}",
        "%%Creator: svgwriter",
        "%%LanguageLevel: 2",
        "%%EndComments",
        "gsave",
    ]
    for item in scene.items:
        if not len(item.data):
            continue
        path = _path(item, scene.height)
        if item.fill is not None:
            r, g, b = item.fill.rgb
            lines += [path, f"{_n(r)} {_n(g)} {_n(b)} setrgbcolor", "eofill" if item.evenodd else "fill"]
        if item.stroke is not None and item.stroke_width > 0:
            r, g, b = item.stroke.rgb
            dashes = " ".join(_n(d) for d in item.dashes)
            lines += [path, f"{_n(r)} {_n(g)} {_n(b)} setrgbcolor", f"{_n(item.stroke_width)} setlinewidth",
                      f"{CAPS.get(item.linecap, 0)} setlinecap {JOINS.get(item.linejoin, 0)} setlinejoin",
                      f"{_n(item.miter_limit)} setmiterlimit [{dashes}] 0 setdash", "stroke"]
    lines += ["grestore", "showpage", "%%EOF"]
    return "\n".join(lines) + "\n"
