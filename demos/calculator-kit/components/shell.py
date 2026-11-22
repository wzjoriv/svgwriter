"""Shell styles: the body behind the display and the keys."""

from collections.abc import Callable

import svgwriter as svg

HARD_SHADOW = 8     # offset of the brutal style's solid shadow
SOFT_SHADOW = 14    # blur of the soft style's shadow
SOLID = {
    "brutal": {"fill": "#ffffff", "stroke": "#000000", "stroke_width": 3},
    "glass": {"fill": "#ffffff", "fill_opacity": 0.35, "stroke": "#ffffff", "stroke_opacity": 0.7,
              "stroke_width": 1.5},
}
"""Fixed paint of the styles that do not take the theme's."""


def _default(body: svg.Rect, accent: svg.Color) -> None:
    body.as_role("box")
    body.filter = svg.filters.drop_shadow(0, 6, 10, opacity=0.25)


def _flat(body: svg.Rect, accent: svg.Color) -> None:
    body.as_role("surface")


def _brutal(body: svg.Rect, accent: svg.Color) -> None:
    body.filter = svg.filters.drop_shadow(HARD_SHADOW, HARD_SHADOW, 0, color="#000000")


def _soft(body: svg.Rect, accent: svg.Color) -> None:
    body.as_role("surface")
    body.filter = svg.filters.drop_shadow(0, 10, SOFT_SHADOW, color=accent.darken(0.3), opacity=0.35)


def _glass(body: svg.Rect, accent: svg.Color) -> None:
    body.filter = svg.filters.drop_shadow(0, 8, 16, color="#1e1b4b", opacity=0.2)


SHELLS: dict[str, Callable[[svg.Rect, svg.Color], None]] = {
    "default": _default, "flat": _flat, "brutal": _brutal, "soft": _soft, "glass": _glass,
}
"""How each style dresses the shell's rect, given the accent colour."""


def shell(style: str, *, radius: float, accent: svg.Color) -> svg.Rect:
    """The shell's background rect in *style*; the layout group sizes it."""
    body = svg.rect(0, 0, 1, 1, rx=radius, **SOLID.get(style, {}))
    SHELLS[style](body, accent)
    return body
