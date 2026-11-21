"""# Logo

An app logo defined in Python, with variants, and every asset generated from it. A project keeps a module
like this one; tooling imports ``logo`` and writes SVG variants, PNGs at any size, ``.ico``/``.icns`` and
favicons. Output is deterministic, so stale assets can be detected by regenerating and comparing.

Run it as ``python 12_logo.py`` or open ``12_logo.ipynb`` to see each variant.
"""

import svgwriter as svg

# %% [markdown]
# The logo is one function of a theme. The ground takes the palette's `primary`, the mark `on_primary`
# and the dot `accent`. A theme whose accent is its primary has a single ink (the built-in `mono`),
# so the mark is cut out of the ground by boolean subtraction instead.

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
logo(svg.Theme.get("light").replace(palette={"primary": "#7c3aed", "accent": "#f472b6"}))

# %% [markdown]
# Every asset a project usually needs comes from that one definition: SVG variants, PNGs at any size,
# a multi-size `.ico`, an `.icns` and an apple-touch icon. This cell only runs when the file is executed, not when it is imported
# (the devkit `logo` tool imports `logo` from here as `examples.12_logo`).

# %%
if __name__ == "__main__":
    for variant in VARIANTS:
        logo(variant).save(f"logo-{variant}.svg")
    light = logo()
    for size in (16, 32, 48, 64, 128, 256, 512, 1024):
        light.save(f"logo-{size}.png", size=size, padding=PADDING)
    light.save("favicon.ico", padding=PADDING, sizes=(16, 32, 48))
    light.save("logo.icns", padding=PADDING)
    light.save("apple-touch-icon.png", padding=PADDING, size=180, background=svg.Theme.get("light").palette.primary)
