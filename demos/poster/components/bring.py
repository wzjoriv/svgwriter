"""What to bring: a row of simple drawn icons, each named under it."""

import svgwriter as svg


def _gloves() -> svg.Group:
    hand = svg.path("M-5 6 L-5 -2 L-4 -7 L-2 -7 L-2 -2 L-1 -8 L1 -8 L1 -2 L2 -7 L4 -7 L4 0 L6 -3 L7 -2 L5 6 Z")
    return svg.Group(hand, svg.rect(-5, 6, 10, 3, rx=1))


def _bag() -> svg.Group:
    return svg.Group(svg.path("M-6 -3 L6 -3 L5 9 L-5 9 Z"), svg.path("M-3 -3 C-3 -9 3 -9 3 -3", fill="none"))


def _bottle() -> svg.Group:
    return svg.Group(svg.rect(-3.5, -4, 7, 13, rx=2), svg.rect(-1.5, -8, 3, 4, rx=0.6))


def _hat() -> svg.Group:
    return svg.Group(svg.ellipse(0, 4, 9, 2.4), svg.path("M-5 4 C-5 -6 5 -6 5 4 Z"))


ITEMS = {"Gloves": _gloves, "Bag": _bag, "Water": _bottle, "Sun hat": _hat}
"""Each thing to bring and the function drawing its icon around (0, 0), about 18 mm across."""


def bring(width: float, *, family: svg.Typeface, gap: float) -> svg.HStack:
    """The icons side by side across *width* mm, each in a soft circle with its name underneath."""
    cells = []
    for name, icon in ITEMS.items():
        badge = svg.Group(svg.circle(0, 0, 11).as_role("badge"), icon().as_role("icon"))
        cells.append(svg.VStack(badge, svg.text(name, font_family=family).as_role("caption"), gap=2.5,
                                align="center"))
    return svg.HStack(*cells, gap=gap, width=width, justify="space-between", align="start")
