"""# Logo

You will build: an app logo in light, dark and mono versions, plus the PNG sizes, favicon and app icons made
from it.

Run it from this folder with ``python logo.py``, or open ``logo.ipynb``.
"""

import svgwriter as svg

# %% [markdown]
# The logo is a function of a theme, so its colours come from the theme's palette. With a single ink
# (the `mono` theme) the mark is cut out of the tile instead.

# %%
SIZE = 100.0
PADDING = 4.0
VARIANTS = ("light", "dark", "mono")


def logo(theme: svg.Theme | str = "light") -> svg.Document:
    """The logo as a document, colored by a theme.

    Parameters
    ----------
    theme : Theme or str
        A theme or the name of a registered one (``"light"``, ``"dark"``, ``"mono"``, ...).

    Returns
    -------
    Document
        A ``SIZE x SIZE`` drawing centred on the origin.
    """
    palette = svg.Theme.of(theme).palette
    doc = svg.Document(root=svg.Svg(view_box=(-SIZE / 2, -SIZE / 2, SIZE, SIZE)))
    ground = svg.rect(-SIZE / 2, -SIZE / 2, SIZE, SIZE, rx=SIZE * 0.22)
    pen = svg.path().move_to(-22, 18).line_to(0, -24).line_to(22, 18)
    mark = pen.to_path(stroke="black", stroke_width=12, fill="none").stroked(12)
    dot = svg.circle(0, 6, 7)
    if palette.accent.hex == palette.primary.hex:
        doc += (ground - mark - dot).update(fill=palette.primary)
        return doc
    doc += ground.update(fill=palette.primary)
    doc += mark.update(fill=palette.on_primary)
    doc += dot.update(fill=palette.accent)
    return doc


# %% [markdown]
# The default light variant.

# %%
logo()

# %% [markdown]
# The dark variant.

# %%
logo("dark")

# %% [markdown]
# The mono variant, a single path.

# %%
logo("mono")

# %% [markdown]
# Any theme works, including a variant made on the spot.

# %%
logo(svg.themes.get("light").replace(palette={"primary": "#7c3aed", "accent": "#f472b6"}))

# %% [markdown]
# Every file a project needs comes from that one function: SVG versions, PNGs at many sizes, a favicon
# and app icons. Next: [21 PowerPoint](../21_powerpoint/powerpoint.py).

# %%
if __name__ == "__main__":
    for variant in VARIANTS:
        logo(variant).save(f"20_logo-{variant}.svg")
    light = logo()
    for size in (16, 32, 48, 64, 128, 256, 512, 1024):
        light.save(f"20_logo-{size}.png", pixels=size, padding=PADDING)
    light.save("20_favicon.ico", padding=PADDING, sizes=(16, 32, 48))
    light.save("20_logo.icns", padding=PADDING)
    light.save("20_apple-touch-icon.png", padding=PADDING, pixels=180, background=svg.themes.get("light").palette.primary)
