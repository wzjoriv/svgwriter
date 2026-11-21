"""A title over a subtitle, fading in."""

import svgwriter as svg


def heading(title: str, subtitle: str, *, x: float, y: float) -> svg.VStack:
    """The heading with its top-left corner at (x, y)."""
    block = svg.VStack(svg.text(title).as_role("title"), svg.text(subtitle).as_role("subtitle"), gap=10)
    block.t = svg.Matrix.translate(x, y)
    return block
