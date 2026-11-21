"""
Excalidraw scenes (``.excalidraw`` JSON) in and out.
"""

from __future__ import annotations

import base64
import json
import math
import random
from typing import TYPE_CHECKING, Any

from ._constants import (
    ANCHORS,
    ARROW_LENGTH,
    ARROW_SPREAD,
    ASCENT,
    EXPORT_FAMILIES,
    EXPORT_TOLERANCE,
    FONTS,
    LINE_HEIGHT,
    OPACITY_SCALE,
    ROUND_FRACTION,
    ROUND_RADIUS,
    SOURCE,
    TRANSPARENT,
)

if TYPE_CHECKING:
    from ....document import Document
    from ....model.elements.core import Element

__all__ = ["read_excalidraw", "to_excalidraw"]


def _paint(value: Any) -> str:
    """An Excalidraw color as an SVG paint (``transparent`` is ``none``)."""
    return "none" if value in (None, TRANSPARENT) else str(value)


def _style(item: dict[str, Any]) -> dict[str, Any]:
    stroke_width = float(item.get("strokeWidth", 2))
    style: dict[str, Any] = {
        "stroke": _paint(item.get("strokeColor", "#1e1e1e")),
        "stroke_width": stroke_width,
        "fill": _paint(item.get("backgroundColor", TRANSPARENT)),
        "stroke_linecap": "round",
        "stroke_linejoin": "round",
    }
    dashes = {"dashed": f"8 {8 + stroke_width:g}", "dotted": f"1.5 {6 + stroke_width:g}"}.get(item.get("strokeStyle", ""))
    if dashes:
        style["stroke_dasharray"] = dashes
    opacity = float(item.get("opacity", OPACITY_SCALE)) / OPACITY_SCALE
    if opacity < 1:
        style["opacity"] = opacity
    return style


def _arrowhead(tip: tuple[float, float], before: tuple[float, float], style: dict[str, Any]) -> Element:
    from ....model.elements.shapes import Path

    angle = math.atan2(tip[1] - before[1], tip[0] - before[0])
    spread = math.radians(ARROW_SPREAD)
    left = (tip[0] - ARROW_LENGTH * math.cos(angle - spread), tip[1] - ARROW_LENGTH * math.sin(angle - spread))
    right = (tip[0] - ARROW_LENGTH * math.cos(angle + spread), tip[1] - ARROW_LENGTH * math.sin(angle + spread))
    return Path(**{**style, "fill": "none"}).move_to(*left).line_to(*tip).line_to(*right)


def _element(item: dict[str, Any], files: dict[str, Any]) -> Element | None:
    from ....model.elements.shapes import Ellipse, Path, Polygon, Rect
    from ....model.elements.structure import Group, Image
    from ....model.elements.text import Text

    kind = item.get("type")
    x, y = float(item.get("x", 0)), float(item.get("y", 0))
    w, h = float(item.get("width", 0)), float(item.get("height", 0))
    style = _style(item)
    element: Element | None
    if kind == "rectangle":
        radius = min(ROUND_RADIUS, ROUND_FRACTION * min(w, h)) if item.get("roundness") else None
        element = Rect(x, y, w, h, rx=radius, **style)
    elif kind == "ellipse":
        element = Ellipse(x + w / 2, y + h / 2, w / 2, h / 2, **style)
    elif kind == "diamond":
        element = Polygon([(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)], **style)
    elif kind in ("line", "arrow", "freedraw"):
        points = [(x + float(px), y + float(py)) for px, py in item.get("points", [])]
        if len(points) < 2:
            return None
        closed = kind == "line" and points[0] == points[-1] and style["fill"] != "none"
        path = Path(**({**style, "fill": style["fill"] if closed else "none"})).move_to(*points[0])
        for point in points[1:]:
            path.line_to(*point)
        if closed:
            path.close()
        heads = [(points[-1], points[-2]) if item.get("endArrowhead") else None,
                 (points[0], points[1]) if item.get("startArrowhead") else None]
        heads = [h for h in heads if h is not None]
        element = Group(path, *(_arrowhead(tip, before, style) for tip, before in heads)) if heads else path
    elif kind == "text":
        size = float(item.get("fontSize", 20))
        anchor = ANCHORS.get(item.get("textAlign", "left"), "start")
        ax = {"start": x, "middle": x + w / 2, "end": x + w}[anchor]
        line_height = float(item.get("lineHeight", LINE_HEIGHT)) * size
        lines = str(item.get("text", "")).split("\n")
        group = Group()
        for index, line in enumerate(lines):
            group.append(Text(line, x=ax, y=y + ASCENT * size + index * line_height, font_size=size,
                              font_family=FONTS.get(int(item.get("fontFamily", 1)), FONTS[1]), text_anchor=anchor,
                              fill=_paint(item.get("strokeColor", "#1e1e1e")), xml_space="preserve",
                              opacity=style.get("opacity")))
        element = group if len(lines) > 1 else group[0].clone()
    elif kind == "image":
        data_url = files.get(item.get("fileId", ""), {}).get("dataURL")
        if not data_url:
            return None
        element = Image(None, x, y, w, h, preserve_aspect_ratio="none", opacity=style.get("opacity"))
        element.set("xlink:href", data_url)
    else:
        return None
    angle = float(item.get("angle", 0.0))
    if angle and element is not None:
        element.rotate(math.degrees(angle), about=(x + w / 2, y + h / 2))  # type: ignore[attr-defined]
    return element


def read_excalidraw(text: str) -> Document:
    """An Excalidraw scene as a document (sloppiness and hachure fills are drawn clean and solid).

    Elements become native SVG: rectangles, ellipses, diamonds (polygons),
    lines and arrows (paths with arrowheads), freedraw, text (one ``<text>``
    per line) and embedded images; ``groupIds`` become nested ``<g>``.

    Parameters
    ----------
    text : str
        The scene JSON.

    Returns
    -------
    Document
        The drawing as native SVG elements.

    Raises
    ------
    ValueError
        If the JSON is not an Excalidraw scene.

    See Also
    --------
    to_excalidraw : Write a scene.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.formats.export._scene._excalidraw import read_excalidraw, to_excalidraw
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> len(read_excalidraw(to_excalidraw(doc)))
    1
    """
    from ....document import Document
    from ....model.elements.structure import A, Group

    scene = json.loads(text)
    if scene.get("type") != "excalidraw":
        raise ValueError("not an Excalidraw scene (missing type: excalidraw)")
    files = scene.get("files", {})
    doc = Document()
    groups: dict[str, Group] = {}
    for item in scene.get("elements", []):
        if item.get("isDeleted"):
            continue
        element = _element(item, files)
        if element is None:
            continue
        parent: Any = doc
        for group_id in reversed(item.get("groupIds", [])):
            if group_id not in groups:
                groups[group_id] = parent.add(Group(id=f"group-{group_id}"))
            parent = groups[group_id]
        parent.add(A(element, href=item["link"]) if item.get("link") else element)
    return doc.fit(padding=10)


def _common(rng: random.Random, number: int, link: str | None) -> dict[str, Any]:
    """The bookkeeping fields every exported Excalidraw element carries."""
    return {"id": f"svgw{number}", "groupIds": [], "roundness": None, "seed": rng.randrange(2 ** 31), "version": 1,
            "versionNonce": rng.randrange(2 ** 31), "isDeleted": False, "boundElements": None, "locked": False,
            "link": link, "roughness": 0}


def _image(image: Any, matrix: Any, rng: random.Random, number: int, files: dict[str, Any]) -> dict[str, Any]:
    """One embedded image as an Excalidraw ``image`` element over its upright page box, its PNG stored in *files*."""
    from ...._internal._render._layers import pixel_box

    box = pixel_box(image, matrix)
    key = f"svgw-image{len(files)}"
    files[key] = {"mimeType": "image/png", "id": key, "created": 0,
                  "dataURL": "data:image/png;base64," + base64.b64encode(image.encode("png")).decode("ascii")}
    return {**_common(rng, number, None), "type": "image", "x": box.x, "y": box.y,
            "width": box.width, "height": box.height, "angle": 0, "fileId": key, "status": "saved",
            "scale": [1, 1], "strokeColor": TRANSPARENT, "backgroundColor": TRANSPARENT,
            "fillStyle": "solid", "strokeWidth": 0, "strokeStyle": "solid", "opacity": 100}


def _text(run: Any, rng: random.Random, number: int) -> dict[str, Any]:
    """One text run as an Excalidraw ``text`` element, turned about its centre like the run."""
    matrix = run.matrix
    stretch = math.sqrt(abs(matrix.determinant))
    size, width = run.size * stretch, run.width * stretch
    height = size * LINE_HEIGHT
    angle = math.atan2(matrix.b, matrix.a)
    top = -size * ASCENT
    centre_x = matrix.e + math.cos(angle) * width / 2 - math.sin(angle) * (top + height / 2)
    centre_y = matrix.f + math.sin(angle) * width / 2 + math.cos(angle) * (top + height / 2)
    family = next((code for word, code in EXPORT_FAMILIES.items() if word in run.family.lower()), 2)
    return {**_common(rng, number, None), "type": "text", "x": centre_x - width / 2, "y": centre_y - height / 2,
            "width": width, "height": height, "angle": angle % math.tau, "text": run.text, "originalText": run.text,
            "fontSize": size, "fontFamily": family, "textAlign": "left", "verticalAlign": "top",
            "lineHeight": LINE_HEIGHT, "containerId": None, "autoResize": True,
            "strokeColor": run.fill.hex if run.fill is not None else TRANSPARENT, "backgroundColor": TRANSPARENT,
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "opacity": round(OPACITY_SCALE * run.opacity)}


def to_excalidraw(document: Document, *, seed: int = 0) -> str:
    """An Excalidraw scene: outlines as ``line`` elements (one per subpath), images and text.

    Parameters
    ----------
    document : Document
        The document to convert.
    seed : int, optional
        Seed for the random ids and seeds Excalidraw stores, so output is reproducible. Defaults to 0.

    Returns
    -------
    str
        The scene as JSON text.

    See Also
    --------
    read_excalidraw : Read a scene back.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.formats.export._scene._excalidraw import to_excalidraw
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> to_excalidraw(doc, seed=1) == to_excalidraw(doc, seed=1)
    True
    """
    from ...._internal._flat._flatten import flatten, polylines

    rng = random.Random(seed)
    files: dict[str, Any] = {}
    elements: list[dict[str, Any]] = []
    scene = flatten(document, handled=frozenset({"image"}), text=True)
    for item in scene.painted():
        if isinstance(item, tuple):
            elements.append(_image(*item, rng, len(elements), files))
            continue
        stroke = item.stroke.hex if item.stroke is not None else TRANSPARENT
        fill = item.fill.hex if item.fill is not None else TRANSPARENT
        opacity = round(OPACITY_SCALE * (item.fill_opacity if item.fill is not None else item.stroke_opacity))
        for points, closed in polylines(item.data, EXPORT_TOLERANCE):
            x0, y0 = points[0]
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            elements.append({
                **_common(rng, len(elements), item.link), "type": "line", "x": x0, "y": y0,
                "width": max(xs) - min(xs), "height": max(ys) - min(ys), "angle": 0,
                "strokeColor": stroke, "backgroundColor": fill if closed else TRANSPARENT,
                "fillStyle": "solid", "strokeWidth": item.stroke_width if item.stroke is not None else 0,
                "strokeStyle": "dashed" if item.dashes else "solid", "opacity": opacity,
                "points": [[px - x0, py - y0] for px, py in points],
                "lastCommittedPoint": None, "startArrowhead": None, "endArrowhead": None,
            })
    elements += [_text(run, rng, len(elements) + index) for index, run in enumerate(scene.texts)]
    return json.dumps({"type": "excalidraw", "version": 2, "source": SOURCE, "elements": elements,
                       "appState": {"viewBackgroundColor": "#ffffff"}, "files": files}, indent=1)
