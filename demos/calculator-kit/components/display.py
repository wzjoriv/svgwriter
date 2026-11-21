"""The display: an optional history line over the current number."""

import svgwriter as svg

FONTS = {
    "serif": "Georgia, 'Times New Roman', serif",
    "mono": "Consolas, 'DejaVu Sans Mono', Menlo, monospace",
    "grotesk": "Inter, 'Segoe UI', Helvetica, Arial, sans-serif",
}
ALIGN = {"left": "start", "center": "center", "right": "end"}


def display(value: str, history: str | None, *, font: str, size: float, align: str, radius: float) -> svg.VStack:
    """The screen: *history* in small type (when given) above *value*, aligned left, centred or right."""
    lines = []
    if history:
        lines.append(svg.text(history, font_family=FONTS[font], font_size=size * 0.4, opacity=0.6)
                     .as_role("readout"))
    lines.append(svg.text(value, font_family=FONTS[font], font_size=size).as_role("readout"))
    return svg.VStack(*lines, gap=size * 0.2, padding=(size * 0.35, size * 0.45), align=ALIGN[align],
                      background=svg.rect(0, 0, 1, 1, rx=radius).as_role("screen"))
