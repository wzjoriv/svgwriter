"""A group of circles melted together by the goo filter, filled with a vertical blend."""

import svgwriter as svg


def body(circles: list[svg.Circle], *, top: str, bottom: str, height: float, melt: float) -> svg.Group:
    """*circles* in one group under ``svg.filters.goo(melt)``: near circles bridge, far ones part.

    The blend runs from *top* at y = 0 to *bottom* at *height* in page units, so every circle shares one
    gradient and a blob keeps its colour where it moves.
    """
    shared = svg.gradients.blend(top, bottom, gradient_units="userSpaceOnUse", x1=0, y1=0, x2=0, y2=height)
    group = svg.Group(*circles, fill=shared)
    group.filter = svg.filters.goo(melt)
    return group
