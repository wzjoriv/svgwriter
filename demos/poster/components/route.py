"""A dashed route through stations, with a marker at every bend and an arrow at the end."""

from collections.abc import Sequence

import svgwriter as svg


def route(stations: Sequence[tuple[str, float, float]], *, family: svg.Typeface) -> svg.Group:
    """The route through *stations* (name, x, y in mm), each named just above its marker."""
    group = svg.Group()
    points = [(x, y) for _, x, y in stations]
    data = f"M{points[0][0]:g} {points[0][1]:g}"
    for (x0, y0), (x1, y1) in zip(points, points[1:], strict=False):
        middle = (x0 + x1) / 2
        data += f" C{middle:g} {y0:g} {middle:g} {y1:g} {x1:g} {y1:g}"
    group += svg.path(data, marker_start=svg.markers.dot(2.4, color="#e2703a"),
                      marker_mid=svg.markers.dot(2.4, color="#e2703a"),
                      marker_end=svg.markers.arrow(3, color="#e2703a")).as_role("route")
    for name, x, y in stations:
        group += svg.text(name, x=x, y=y - 3.5, text_anchor="middle", font_family=family,
                          fill="#ffffff").as_role("caption")
    return group
