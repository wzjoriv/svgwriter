"""
DrawingML paints and line styles: SVG gradients, dashes, caps and joins to and from ``<a:gradFill>`` and ``<a:ln>``.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from ._constants import A_NS, ALPHA_SCALE, ANGLE_UNIT, CAPS, JOINS, MITER_SCALE

if TYPE_CHECKING:
    from ..._internal._paints import Shading
    from ...elements.core import Element
    from ...pathdata.data import BBox

__all__ = ["gradient_xml", "line_style", "read_gradient", "read_line_style"]

Rgba = tuple[float, float, float, float]


def _a(tag: str) -> str:
    return f"{{{A_NS}}}{tag}"


def _at(stops: list[tuple[float, Rgba]], t: float) -> Rgba:
    """The padded colour of a stop list at offset *t*."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (o0, c0), (o1, c1) in zip(stops, stops[1:], strict=False):
        if t <= o1:
            k = (t - o0) / (o1 - o0) if o1 > o0 else 1.0
            return tuple(a + (b - a) * k for a, b in zip(c0, c1, strict=True))  # type: ignore[return-value]
    return stops[-1][1]


def _reposition(stops: list[tuple[float, Rgba]], low: float, high: float) -> list[tuple[float, Rgba]]:
    """Stops re-expressed over ``low..high`` of the original offsets, with end stops for the padding."""
    span = high - low or 1.0
    inner = [((o - low) / span, c) for o, c in stops if low < o < high]
    return [(0.0, _at(stops, low)), *inner, (1.0, _at(stops, high))]


def gradient_xml(shading: Shading, box: BBox, opacity: float) -> str:
    """``<a:gradFill>`` for a flattened gradient fill over the page box *box*.

    Parameters
    ----------
    shading : Shading
        The gradient with its page matrix.
    box : BBox
        The filled outline's page box; DrawingML stretches gradients over it.
    opacity : float
        Fill opacity multiplied into every stop.

    Returns
    -------
    str
        The fill, with its namespace declared. Linear gradients are exact;
        radial ones are centred on the gradient centre and reach its radius.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._flatten import flatten
    >>> from svgwriter.export._office._drawingml import gradient_xml
    >>> doc = svg.Document(100, 50)
    >>> _ = doc.rect(0, 0, 100, 50, fill=svg.LinearGradient.horizontal("red", "blue"))
    >>> item = flatten(doc).items[0]
    >>> '<a:lin ang="0" scaled="0"/>' in gradient_xml(item.shading, item.data.bbox, 1.0)
    True
    """
    stops = [(offset, tuple(c / 255 for c in color.uint8)) for offset, color in shading.stops]
    matrix = shading.matrix
    corners = [(box.x, box.y), (box.x + box.width, box.y), (box.x, box.y + box.height),
               (box.x + box.width, box.y + box.height)]
    if shading.kind == "axial":
        x1, y1, x2, y2 = shading.coords[:4]
        dx, dy = x2 - x1, y2 - y1
        length = dx * dx + dy * dy or 1.0
        inverse = matrix.inverse()
        gx = (inverse.a * dx + inverse.b * dy) / length
        gy = (inverse.c * dx + inverse.d * dy) / length

        def param(x: float, y: float) -> float:
            u, v = inverse.apply(x, y)
            return ((u - x1) * dx + (v - y1) * dy) / length

        values = [param(x, y) for x, y in corners]
        placed = _reposition(stops, min(values), max(values))
        angle = round(math.degrees(math.atan2(gy, gx)) % 360 * ANGLE_UNIT)
        shape = f'<a:lin ang="{angle}" scaled="0"/>'
    else:
        cx, cy, radius = shading.coords[3:6]
        centre_x, centre_y = matrix.apply(cx, cy)
        reach = max(math.hypot(x - centre_x, y - centre_y) for x, y in corners) or 1.0
        placed = _reposition(stops, 0.0, reach / (radius * math.sqrt(abs(matrix.determinant)) or 1.0))
        left = round((centre_x - box.x) / (box.width or 1.0) * ALPHA_SCALE)
        top = round((centre_y - box.y) / (box.height or 1.0) * ALPHA_SCALE)
        shape = (f'<a:path path="circle"><a:fillToRect l="{left}" t="{top}" r="{ALPHA_SCALE - left}" '
                 f'b="{ALPHA_SCALE - top}"/></a:path>')
    entries = "".join(
        f'<a:gs pos="{round(offset * ALPHA_SCALE)}"><a:srgbClr val="{_hex(color)}">'
        f'<a:alpha val="{round(color[3] * opacity * ALPHA_SCALE)}"/></a:srgbClr></a:gs>'
        for offset, color in placed)
    return f'<a:gradFill xmlns:a="{A_NS}" rotWithShape="1"><a:gsLst>{entries}</a:gsLst>{shape}</a:gradFill>'


def _hex(color: Rgba) -> str:
    return "".join(f"{round(channel * 255):02X}" for channel in color[:3])


def line_style(line: Any, width: float, dashes: tuple[float, ...], cap: str, join: str, miter: float) -> None:
    """Add dashes, cap and join to an ``<a:ln>`` that already holds its fill.

    Parameters
    ----------
    line : lxml element
        The ``<a:ln>``.
    width : float
        Stroke width, in the same units as *dashes*.
    dashes : tuple of float
        SVG dash lengths; empty for a solid line.
    cap, join : str
        ``stroke-linecap`` and ``stroke-linejoin``.
    miter : float
        ``stroke-miterlimit``.

    Examples
    --------
    >>> from lxml import etree
    >>> from svgwriter.export._office._drawingml import line_style
    >>> line = etree.Element("{http://schemas.openxmlformats.org/drawingml/2006/main}ln")
    >>> line_style(line, 2.0, (4.0, 2.0), "round", "bevel", 4.0)
    >>> line.get("cap"), [child.tag.split("}")[1] for child in line]
    ('rnd', ['custDash', 'bevel'])
    """
    line.set("cap", CAPS.get(cap, "flat"))
    if dashes and width > 0:
        pattern = list(dashes) * (2 if len(dashes) % 2 else 1)
        custom = line.makeelement(_a("custDash"), {})
        for dash, space in zip(pattern[::2], pattern[1::2], strict=True):
            custom.append(line.makeelement(_a("ds"), {"d": str(round(dash / width * ALPHA_SCALE)),
                                                     "sp": str(round(space / width * ALPHA_SCALE))}))
        line.append(custom)
    tag = JOINS.get(join, "miter")
    attributes = {"lim": str(round(miter * MITER_SCALE))} if tag == "miter" else {}
    line.append(line.makeelement(_a(tag), attributes))


def read_line_style(path: Element, line: Any, width: float) -> None:
    """Copy an ``<a:ln>``'s dashes, cap and join onto *path* (the inverse of :func:`line_style`).

    Parameters
    ----------
    path : Element
        The stroked element.
    line : lxml element
        The ``<a:ln>``.
    width : float
        The stroke width in user units.

    Examples
    --------
    >>> from lxml import etree
    >>> import svgwriter as svg
    >>> from svgwriter.export._office._drawingml import line_style, read_line_style
    >>> line = etree.Element("{http://schemas.openxmlformats.org/drawingml/2006/main}ln")
    >>> line_style(line, 2.0, (4.0, 2.0), "round", "round", 4.0)
    >>> path = svg.path("M0 0 L10 0")
    >>> read_line_style(path, line, 2.0)
    >>> path.get("stroke-dasharray"), path.get("stroke-linecap"), path.get("stroke-linejoin")
    ('4 2', 'round', 'round')
    """
    caps = {value: key for key, value in CAPS.items()}
    if line.get("cap") in caps and line.get("cap") != "flat":
        path.set("stroke-linecap", caps[line.get("cap")])
    custom = line.find(_a("custDash"))
    if custom is not None:
        lengths = [int(segment.get(name, 0)) / ALPHA_SCALE * width for segment in custom.iter(_a("ds"))
                   for name in ("d", "sp")]
        if lengths:
            path.set("stroke-dasharray", " ".join(f"{round(value, 3):g}" for value in lengths))
    for name, tag in JOINS.items():
        if tag != "miter" and line.find(_a(tag)) is not None:
            path.set("stroke-linejoin", name)


def read_gradient(fill: Any, left: float, top: float, width: float, height: float) -> Element | None:
    """A ``userSpaceOnUse`` gradient for an ``<a:gradFill>`` over the shape box, or None.

    Parameters
    ----------
    fill : lxml element
        The ``<a:gradFill>``.
    left, top, width, height : float
        The shape's box in user units.

    Returns
    -------
    Element or None
        A linear gradient for ``<a:lin>`` (and for fills without a shade
        shape), a radial one for ``<a:path>``; None without explicit RGB stops.

    Examples
    --------
    >>> from lxml import etree
    >>> from svgwriter.export._office._drawingml import read_gradient
    >>> xml = ('<a:gradFill xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:gsLst>'
    ...        '<a:gs pos="0"><a:srgbClr val="FF0000"/></a:gs><a:gs pos="100000"><a:srgbClr val="0000FF"/></a:gs>'
    ...        '</a:gsLst><a:lin ang="0" scaled="0"/></a:gradFill>')
    >>> gradient = read_gradient(etree.fromstring(xml), 0, 0, 100, 50)
    >>> gradient.tag, gradient.get("x1"), gradient.get("x2")
    ('linearGradient', 0.0, 100.0)
    """
    from ...color.color import Color
    from ...elements.paint import LinearGradient, RadialGradient, Stop

    stops = []
    for entry in fill.iter(_a("gs")):
        rgb = entry.find(_a("srgbClr"))
        if rgb is None:
            return None
        alpha = rgb.find(_a("alpha"))
        color = Color.parse("#" + rgb.get("val"))
        stops.append(Stop(int(entry.get("pos", 0)) / ALPHA_SCALE, color,
                          stop_opacity=int(alpha.get("val")) / ALPHA_SCALE if alpha is not None else None))
    if not stops:
        return None
    centre_x, centre_y = left + width / 2, top + height / 2
    shade = fill.find(_a("path"))
    if shade is not None:
        rect = shade.find(_a("fillToRect"))
        fx = left + int(rect.get("l", ALPHA_SCALE // 2)) / ALPHA_SCALE * width if rect is not None else centre_x
        fy = top + int(rect.get("t", ALPHA_SCALE // 2)) / ALPHA_SCALE * height if rect is not None else centre_y
        reach = max(math.hypot(x - fx, y - fy) for x in (left, left + width) for y in (top, top + height))
        return RadialGradient(*stops, cx=fx, cy=fy, r=reach, gradient_units="userSpaceOnUse")
    linear = fill.find(_a("lin"))
    turn = math.radians(int(linear.get("ang", 0)) / ANGLE_UNIT) if linear is not None else 0.0
    ux, uy = math.cos(turn), math.sin(turn)
    half = (abs(width * ux) + abs(height * uy)) / 2
    return LinearGradient(*stops, x1=centre_x - ux * half, y1=centre_y - uy * half, x2=centre_x + ux * half,
                          y2=centre_y + uy * half, gradient_units="userSpaceOnUse")
