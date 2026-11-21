"""The legend: one patterned swatch per kind of ground, in a row that fills the given width."""

import svgwriter as svg

GROUNDS = {
    "Sand": svg.patterns.dots(gap=2.2, radius=0.45),
    "Shingle": svg.patterns.crosshatch(gap=2.0, width=0.3),
    "Salt marsh": svg.patterns.hatch(angle=-60, gap=1.6, width=0.35),
    "Rock": svg.patterns.zigzag(wavelength=3.2, amplitude=0.9, gap=2.2, width=0.4),
}
"""Each ground and the pattern that marks it on the map; sizes are millimetres."""


def legend(width: float, *, swatch: float, gap: float, family: svg.Typeface) -> svg.HStack:
    """The swatches side by side across *width* mm, each *swatch* mm tall with its name under it."""
    cells = []
    for name, paint in GROUNDS.items():
        tile = svg.rect(width=1, height=swatch, rx=1.5, fill=paint, stroke="#c9bfae", stroke_width=0.3)
        caption = svg.text(name, font_family=family).as_role("caption")
        cells.append(svg.VStack(tile, caption, gap=2.5, align="stretch"))
    row = svg.HStack(*cells, gap=gap, width=width, align="start")
    for cell in cells:
        cell.width = (width - gap * (len(cells) - 1)) / len(cells)
    return row
