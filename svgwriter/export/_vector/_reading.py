"""
Painted outlines shared by the PDF, EPS and TikZ readers, and the document they become.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final

from ...color.color import Color

if TYPE_CHECKING:
    from ...document import Document
    from ...elements.shapes import Path
    from ...transform.matrix import Matrix

__all__ = ["BLACK", "HAIRLINE", "Outline", "Shape", "cmyk_to_rgb", "string_end", "to_document"]

Op = tuple[str, tuple[float, ...]]
RGB = tuple[float, float, float]

BLACK: Final = (0.0, 0.0, 0.0)
DEFAULT_MITER: Final = 4.0
HAIRLINE: Final = 0.25
MAX_ARC_SEGMENT: Final = math.pi / 2
BEZIER_ARC_FACTOR: Final = 4.0 / 3.0


@dataclass
class Shape:
    """One painted outline in SVG coordinates with solid paints.

    Attributes
    ----------
    ops : list of (str, tuple of float)
        ``M``/``L``/``C``/``Z`` operations with absolute coordinates.
    fill, stroke : tuple of float or None
        RGB paints in 0-1; None means no paint.
    fill_opacity, stroke_opacity : float
        Opacity of each paint.
    evenodd : bool
        Whether the fill uses the even-odd rule.
    stroke_width : float
        Stroke width in user units.
    linecap, linejoin : str
        ``stroke-linecap`` and ``stroke-linejoin`` values.
    miter_limit : float
        ``stroke-miterlimit``.
    dashes : tuple of float
        Dash lengths; empty for a solid stroke.

    See Also
    --------
    to_document : Turn shapes into a document.

    Examples
    --------
    >>> from svgwriter.export._vector._reading import Shape
    >>> Shape([("M", (0.0, 0.0)), ("L", (1.0, 1.0))], stroke=(1.0, 0.0, 0.0)).visible
    True
    """

    ops: list[Op]
    fill: RGB | None = None
    stroke: RGB | None = None
    fill_opacity: float = 1.0
    stroke_opacity: float = 1.0
    evenodd: bool = False
    stroke_width: float = 1.0
    linecap: str = "butt"
    linejoin: str = "miter"
    miter_limit: float = DEFAULT_MITER
    dashes: tuple[float, ...] = field(default=())
    clip: list[Op] | None = None

    @property
    def visible(self) -> bool:
        """Whether the shape has a paint and draws more than move-tos."""
        painted = self.fill is not None or (self.stroke is not None and self.stroke_width > 0)
        return painted and any(op != "M" for op, _ in self.ops)


class Outline:
    """A path under construction, kept in output coordinates.

    Each method maps its user-space arguments through *matrix* first, so the
    caller's current transform is applied when a segment is added.

    See Also
    --------
    Shape : What a finished outline is painted into.

    Examples
    --------
    >>> from svgwriter.transform.matrix import IDENTITY
    >>> from svgwriter.export._vector._reading import Outline
    >>> outline = Outline()
    >>> outline.rect(IDENTITY, 0, 0, 2, 1)
    >>> [op for op, _ in outline.take()]
    ['M', 'L', 'L', 'L', 'Z']
    """

    def __init__(self) -> None:
        self.ops: list[Op] = []
        self.current: tuple[float, float] | None = None
        self.start: tuple[float, float] | None = None

    def move(self, matrix: Matrix, x: float, y: float) -> None:
        """Start a subpath at (*x*, *y*)."""
        point = tuple(matrix.apply(x, y))
        self.ops.append(("M", point))
        self.current = self.start = point

    def line(self, matrix: Matrix, x: float, y: float) -> None:
        """Line to (*x*, *y*), or start a subpath there when there is no current point."""
        if self.current is None:
            self.move(matrix, x, y)
            return
        self.current = tuple(matrix.apply(x, y))
        self.ops.append(("L", self.current))

    def curve(self, matrix: Matrix, *coords: float) -> None:
        """Cubic Bézier through the two control points of *coords* to its last point."""
        if self.current is None:
            self.move(matrix, coords[0], coords[1])
        points = [matrix.apply(coords[i], coords[i + 1]) for i in range(0, 6, 2)]
        self.ops.append(("C", tuple(v for point in points for v in point)))
        self.current = tuple(points[-1])

    def close(self) -> None:
        """Close the current subpath."""
        if self.current is not None:
            self.ops.append(("Z", ()))
            self.current = self.start

    def rect(self, matrix: Matrix, x: float, y: float, width: float, height: float) -> None:
        """A closed rectangle subpath."""
        self.move(matrix, x, y)
        for px, py in ((x + width, y), (x + width, y + height), (x, y + height)):
            self.line(matrix, px, py)
        self.close()

    def arc(self, matrix: Matrix, center: tuple[float, float], radii: tuple[float, float],
            start: float, sweep: float, *, connect: bool = True) -> None:
        """Elliptical arc of *sweep* radians from angle *start*, as cubics of at most 90 degrees."""
        (cx, cy), (rx, ry) = center, radii
        x0, y0 = cx + rx * math.cos(start), cy + ry * math.sin(start)
        (self.line if connect and self.current is not None else self.move)(matrix, x0, y0)
        steps = max(1, math.ceil(abs(sweep) / MAX_ARC_SEGMENT - 1e-9))
        step = sweep / steps
        k = BEZIER_ARC_FACTOR * math.tan(step / 4)
        for i in range(steps):
            a, b = start + i * step, start + (i + 1) * step
            self.curve(matrix, cx + rx * (math.cos(a) - k * math.sin(a)), cy + ry * (math.sin(a) + k * math.cos(a)),
                       cx + rx * (math.cos(b) + k * math.sin(b)), cy + ry * (math.sin(b) - k * math.cos(b)),
                       cx + rx * math.cos(b), cy + ry * math.sin(b))

    def user_current(self, matrix: Matrix) -> tuple[float, float] | None:
        """The current point mapped back into the user space of *matrix*."""
        if self.current is None:
            return None
        return tuple(matrix.inverse().apply(*self.current))

    def copy(self) -> Outline:
        """An independent copy, for graphics states that save the current path."""
        twin = Outline()
        twin.ops, twin.current, twin.start = list(self.ops), self.current, self.start
        return twin

    def take(self) -> list[Op]:
        """Return the operations and start an empty path."""
        ops, self.ops = self.ops, []
        self.current = self.start = None
        return ops


def cmyk_to_rgb(c: float, m: float, y: float, k: float) -> RGB:
    """Naive device CMYK to RGB, as PostScript and PDF viewers do without a profile."""
    return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))


def string_end(data: bytes, start: int) -> int:
    """Index just past the ``)`` closing the literal string whose ``(`` precedes *start*."""
    depth, i = 1, start
    while i < len(data):
        char = data[i]
        if char == 0x5C:
            i += 2
            continue
        depth += {0x28: 1, 0x29: -1}.get(char, 0)
        i += 1
        if depth == 0:
            return i
    return len(data)


def _hex(rgb: RGB) -> str:
    """``#rrggbb`` of an RGB triple, clamped to 0-1."""
    return Color(*(min(1.0, max(0.0, v)) for v in rgb)).hex


def _style(shape: Shape) -> dict[str, object]:
    """Path keyword arguments: paints, stroke geometry and opacity."""
    style: dict[str, object] = {"fill": "none" if shape.fill is None else _hex(shape.fill)}
    if shape.evenodd and shape.fill is not None:
        style["fill_rule"] = "evenodd"
    stroked = shape.stroke is not None and shape.stroke_width > 0
    if stroked:
        style.update(stroke=_hex(shape.stroke), stroke_width=shape.stroke_width)
        if shape.linecap != "butt":
            style["stroke_linecap"] = shape.linecap
        if shape.linejoin != "miter":
            style["stroke_linejoin"] = shape.linejoin
        if shape.miter_limit != DEFAULT_MITER:
            style["stroke_miterlimit"] = shape.miter_limit
        if shape.dashes and any(shape.dashes):
            style["stroke_dasharray"] = " ".join(f"{d:g}" for d in shape.dashes)
    opacities = {shape.fill_opacity} if shape.fill is not None else set()
    opacities |= {shape.stroke_opacity} if stroked else set()
    if len(opacities) == 1 and min(opacities) < 1:
        style["opacity"] = min(opacities)
    elif len(opacities) > 1:
        style.update({name: value for name, value in (("fill_opacity", shape.fill_opacity),
                                                      ("stroke_opacity", shape.stroke_opacity)) if value < 1})
    return style


def _path(shape: Shape) -> Path:
    """A ``<path>`` element drawing *shape*."""
    from ...elements.shapes import Path

    path = Path(**_style(shape))
    for op, args in shape.ops:
        if op == "M":
            path.move_to(*args)
        elif op == "L":
            path.line_to(*args)
        elif op == "C":
            path.curve_to(*args)
        else:
            path.close()
    return path


def _merged(shapes: list[Any]) -> list[Any]:
    """Visible shapes, a stroke-only shape folded into the fill-only shape just before it with the same outline.

    Ready-made elements (images, text) pass through in paint order.
    """
    out: list[Any] = []
    for shape in shapes:
        if not isinstance(shape, Shape):
            out.append(shape)
            continue
        if not shape.visible:
            continue
        previous = out[-1] if out else None
        if (isinstance(previous, Shape) and previous.stroke is None and shape.fill is None
                and previous.ops == shape.ops and previous.clip == shape.clip):
            shape.fill, shape.fill_opacity, shape.evenodd = previous.fill, previous.fill_opacity, previous.evenodd
            out[-1] = shape
            continue
        out.append(shape)
    return out


def to_document(shapes: list[Any], view: tuple[float, float, float, float] | None = None) -> Document:
    """A document of ``<path>`` elements, sized to *view* or, without one, fitted to the content.

    Parameters
    ----------
    shapes : list of Shape or Element
        The outlines in paint order; elements (images, text) are added as they are.
    view : tuple of float, optional
        ``(min_x, min_y, width, height)`` of the page in user units. Defaults to None.

    Returns
    -------
    Document
        One path per visible shape.

    See Also
    --------
    Shape : The painted outlines.

    Notes
    -----
    A stroke-only shape directly after a fill-only shape with the same
    outline becomes one path with both paints, undoing how PostScript-like
    formats paint a filled and stroked shape in two passes.

    Examples
    --------
    >>> from svgwriter.export._vector._reading import Shape, to_document
    >>> square = [("M", (0.0, 0.0)), ("L", (4.0, 0.0)), ("L", (4.0, 4.0)), ("Z", ())]
    >>> doc = to_document([Shape(square, fill=(1.0, 0.0, 0.0)), Shape(square, stroke=(0.0, 0.0, 0.0))], (0, 0, 4, 4))
    >>> len(doc), doc[0].get("fill"), doc[0].get("stroke")
    (1, '#ff0000', '#000000')
    """
    from ...document import Document

    if view is None:
        doc = Document()
    else:
        doc = Document(view[2], view[3], view_box=view)
    for shape in _merged(shapes):
        if not isinstance(shape, Shape):
            doc.add(shape)
            continue
        path = _path(shape)
        if shape.clip:
            path.clip(_path(Shape(shape.clip)))
        doc.add(path)
    return doc.fit() if view is None else doc

