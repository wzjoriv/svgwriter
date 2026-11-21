"""# Tide atlas

An A4 print poster drawn in millimetres: `size = "a4"` in `svgwriter.toml` makes every coordinate below
a millimetre, so the PDF prints at true size and the PNG comes out at 300 dpi.
"""

# %%
from components import legend, route, tide_table

import svgwriter as svg

DISPLAY = svg.Typeface("serif")       # the title face; drop an OFL font into assets/fonts to change it
TEXT = svg.Typeface("sans-serif")     # captions and labels
MARGIN = 16
HORIZON = 102                         # where the sky meets the sea
SHORE = 172                           # where the sea meets the legend
STATIONS = (("Gull Point", 30, 132), ("The Narrows", 76, 148), ("Seal Rock", 120, 122),
            ("Long Strand", 158, 154), ("Lantern", 188, 132))

themes = {
    "project": {},
    "night": {"background": "#0f1b24", "foreground": "#eef2f4", "muted": "#9fb0b8", "border": "#33505f"},
    "blueprint": {"background": "#16397a", "foreground": "#e8f0ff", "muted": "#a9c1ee", "border": "#4f78c4",
                  "primary": "#7fb0ff", "secondary": "#ffd166", "accent": "#ffffff"},
    "mint": {"background": "#eaf6ef", "foreground": "#17342a", "muted": "#58786a", "border": "#b6d6c4",
             "primary": "#1b7f5c", "secondary": "#d9822b", "accent": "#f2c14e"},
}
ACCENTS = ("primary", "secondary", "accent")

# %% [markdown]
# Gradients paint the sky and the sea, the `waves` pattern rolls across the water, and the route uses
# markers sized in stroke widths. The legend is an `HStack` of patterned swatches. Three controls restyle
# the poster: the colour theme (`project` keeps `theme.toml`), a hue shift of the theme's accent colours and the
# title.

# %%
@svg.widgets.controls(
    theme=svg.widgets.Segmented(list(themes), value="project"),
    hue=svg.widgets.Slider(-180, 180, step=5, value=0, format="{:.0f}°", label="accent hue shift"),
    title=svg.widgets.Text("Tide"),
)
def poster(doc: svg.Document, *, theme: str = "project", hue: float = 0, title: str = "Tide") -> svg.Document:
    """Draw the poster in the chosen theme, with its accent colours turned *hue* degrees."""
    if theme != "project":
        doc.theme = doc.theme.replace(palette=themes[theme])
    if hue:
        palette = doc.theme.palette
        doc.theme = doc.theme.replace(palette={name: palette[name].hue_shift(hue) for name in ACCENTS})
    box = doc.root.get("viewBox")
    width = box.width
    doc.rect(0, 0, width, box.height).as_role("background")

    doc.rect(0, 0, width, HORIZON, fill=svg.gradients.sunset(angle=90))
    doc.circle(width * 0.72, HORIZON - 4, 24, fill="#fde68a", opacity=0.9)
    doc.circle(width * 0.72, HORIZON - 4, 24, fill=svg.patterns.dots(gap=2.4, radius=0.5, color="#f59e0b"))
    doc.rect(0, HORIZON, width, SHORE - HORIZON, fill=svg.gradients.ocean(angle=90))
    doc.rect(0, HORIZON, width, SHORE - HORIZON,
             fill=svg.patterns.waves(wavelength=9, amplitude=1.1, gap=4.5, width=0.35, color="#ffffff"),
             opacity=0.35)

    doc.text(title, x=MARGIN, y=48, font_family=DISPLAY, font_style="italic").as_role("title")
    doc.text("ATLAS", x=MARGIN + 2, y=64, font_family=TEXT, font_size=9, letter_spacing=4.5,
             fill="#ffffff", font_weight="bold")
    doc.text("A field poster of the northern coast", x=MARGIN + 2, y=74, font_family=TEXT,
             fill="#ffffff").as_role("subtitle")

    doc += route(STATIONS, family=TEXT)

    doc.text("Grounds", x=MARGIN, y=SHORE + 14, font_family=DISPLAY).as_role("subtitle")
    key = legend(width - 2 * MARGIN, swatch=20, gap=6, family=TEXT)
    key.t = svg.Matrix.translate(MARGIN, SHORE + 19)
    doc += key

    doc.text("Tides today", x=MARGIN, y=SHORE + 60, font_family=DISPLAY).as_role("subtitle")
    table = tide_table(width - 2 * MARGIN, family=TEXT, gap=1.6)
    table.t = svg.Matrix.translate(MARGIN, SHORE + 65)
    doc += table

    doc.line(MARGIN, box.height - 20, width - MARGIN, box.height - 20, stroke="#c9bfae", stroke_width=0.3)
    doc.text("Distances not to scale · Printed on A4, 210 × 297 mm", x=MARGIN, y=box.height - 13,
             font_family=TEXT).as_role("caption")
    doc.text("svgwriter", x=width - MARGIN, y=box.height - 13, text_anchor="end",
             font_family=TEXT).as_role("caption")
    return doc


# %%
if __name__ == "__main__":
    print(*svg.Project.load().build(), sep="\n")
