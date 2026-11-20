"""
matplotlib interop: svgwriter elements drawn onto matplotlib axes as native, editable artists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

import numpy as np

if TYPE_CHECKING:
    from ..document import Document
    from ..elements.base import Element

__all__ = ["to_matplotlib"]

MOVETO: Final = 1
LINETO: Final = 2
CURVE4: Final = 4
CLOSEPOLY: Final = 79
POINTS_PER_UNIT: Final = 0.75


def _codes(data: Any) -> tuple[np.ndarray, np.ndarray]:
    """Vertices and matplotlib path codes for path data (curves as cubic Béziers)."""
    from ..pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo
    from ._skia import from_skia, to_skia

    vertices: list[tuple[float, float]] = []
    codes: list[int] = []
    start = here = (0.0, 0.0)
    for command in from_skia(to_skia(data)):
        if isinstance(command, MoveTo):
            start = here = (command.x, command.y)
            vertices.append(here)
            codes.append(MOVETO)
        elif isinstance(command, LineTo):
            here = (command.x, command.y)
            vertices.append(here)
            codes.append(LINETO)
        elif isinstance(command, QuadTo):
            q, end = (command.x1, command.y1), (command.x, command.y)
            vertices += [(here[0] + 2 / 3 * (q[0] - here[0]), here[1] + 2 / 3 * (q[1] - here[1])),
                         (end[0] + 2 / 3 * (q[0] - end[0]), end[1] + 2 / 3 * (q[1] - end[1])), end]
            codes += [CURVE4] * 3
            here = end
        elif isinstance(command, CurveTo):
            here = (command.x, command.y)
            vertices += [(command.x1, command.y1), (command.x2, command.y2), here]
            codes += [CURVE4] * 3
        elif isinstance(command, ClosePath):
            vertices.append(start)
            codes.append(CLOSEPOLY)
            here = start
    return np.array(vertices, dtype=float).reshape(-1, 2), np.array(codes, dtype=np.uint8)


def to_matplotlib(item: Element | Document, ax: Any, *, flip: bool = True) -> list[Any]:
    """Draw an element or document onto matplotlib axes as ``PathPatch`` artists.

    Outlines keep their curves, solid fill and stroke colors, opacity and
    stroke width; each artist stays editable in matplotlib (``set_facecolor``
    and so on). Gradients and patterns become their first color, as in the
    other vector exports.

    Parameters
    ----------
    item : Element or Document
        What to draw.
    ax : matplotlib.axes.Axes
        Target axes; data coordinates are svgwriter user units.
    flip : bool, optional
        Point the y axis down like SVG by inverting the axes' y limits.
        Defaults to True.

    Returns
    -------
    list of matplotlib.patches.PathPatch
        The artists added, in paint order.

    Raises
    ------
    ImportError
        If matplotlib is not installed.

    See Also
    --------
    svgwriter.Document.add : The other direction (figures into documents).

    Examples
    --------
    >>> import svgwriter as svg
    >>> # import matplotlib.pyplot as plt; fig, ax = plt.subplots()
    >>> # svg.ops.to_matplotlib(svg.star(0, 0, 10, fill="gold"), ax)
    """
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MplPath

    from ..document import Document
    from ..export._flatten import flatten

    document = item if isinstance(item, Document) else Document()
    if not isinstance(item, Document):
        document.add(item.clone())
    scene = flatten(document)
    artists = []
    for entry in scene.items:
        vertices, codes = _codes(entry.data)
        if not len(codes):
            continue
        face = (*entry.fill.rgb, entry.fill_opacity) if entry.fill is not None else "none"
        edge = (*entry.stroke.rgb, entry.stroke_opacity) if entry.stroke is not None else "none"
        patch = PathPatch(MplPath(vertices, codes), facecolor=face, edgecolor=edge,
                          linewidth=entry.stroke_width * POINTS_PER_UNIT if entry.stroke is not None else 0)
        ax.add_patch(patch)
        artists.append(patch)
    if artists:
        ax.autoscale_view()
        if flip and not ax.yaxis_inverted():
            ax.invert_yaxis()
        ax.set_aspect("equal")
    return artists
