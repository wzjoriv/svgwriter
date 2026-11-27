"""One key: a label centred on a shaped background."""

from collections.abc import Mapping

import svgwriter as svg

SHAPES = {"sharp": 0.0, "rounded": 0.2, "round": 0.35, "pill": 0.5, "circle": 0.5}
"""Corner radius of each key shape, as a share of the key height."""
OPERATORS = frozenset("÷×−+=")
PRESSED_OPACITY = 0.6
"""Key background opacity while the key is pressed (a short flash; SVG viewers only)."""
PRESS_SECONDS = 0.15
"""Length of the press flash."""
FUNCTIONS = frozenset({"C", "±", "%", "(", ")", "sin", "cos", "tan", "log", "ln", "x²", "√", "π"})


def kind(label: str) -> str:
    """``"operator"``, ``"function"`` or ``"digit"``: which colours the key takes."""
    return "operator" if label in OPERATORS else "function" if label in FUNCTIONS else "digit"


def key(label: str, *, shape: str, height: float, colors: Mapping[str, tuple[svg.Color, svg.Color]],
        font: str, weight: int) -> svg.VStack:
    """The key for *label*, filled and inked from ``colors[kind(label)]``.

    A ``circle`` key is as wide as it is tall; every other shape fills its grid cell.
    """
    fill, ink = colors[kind(label)]
    background = svg.rect(0, 0, 1, 1, rx=height * SHAPES[shape], fill=fill)
    text = svg.text(label, fill=ink, font_family=font, font_weight=weight).as_role("text")
    square = height if shape == "circle" else None
    stack = svg.VStack(text, width=square, height=height, align="center", justify="center", background=background)
    background.animate.on("press", stack).tween("opacity", 1, PRESSED_OPACITY, PRESS_SECONDS, freeze=False)
    return stack
