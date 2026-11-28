"""# Themes

You will build: one small diagram drawn in every built-in theme, and a sheet showing them all side by side.

Run it from this folder with ``python themes.py``, or open ``themes.ipynb``.
"""

import svgwriter as svg

# %% [markdown]
# Instead of colours, give shapes a role such as `as_role("box")` or `as_role("title")`. The theme decides
# how each role looks, so one drawing can wear many looks. Shapes from `svg.paths` come with a role already.

# %%
WIDTH, HEIGHT = 320, 190
SHADOW = 4


def card(theme: svg.Theme | str = "light") -> svg.Document:
    """A small diagram drawn only with roles."""
    doc = svg.Document(WIDTH, HEIGHT, theme=theme)
    doc.rect(0, 0, WIDTH, HEIGHT, rx=12).as_role("background")
    doc.text("Pipeline", x=20, y=38).as_role("title")
    doc.text(f"theme: {doc.theme.name}", x=20, y=60).as_role("caption")
    for index, label in enumerate(("read", "draw", "save")):
        x = 20 + index * 100
        doc.rect(x + SHADOW, 90 + SHADOW, 80, 50, rx=8).as_role("shadow")
        doc.rect(x, 90, 80, 50, rx=8).as_role("box")
        doc.text(label, x=x + 40, y=120, text_anchor="middle").as_role("text")
        if index:
            doc += svg.paths.arrow(x - 18, 115, x - 2, 115, head=6)
    for index in range(3):
        doc += svg.paths.dot(26 + index * 16, 166, 5)
    doc.rect(220, 154, 80, 24, rx=12).as_role("shape")
    doc.text("done", x=260, y=171, text_anchor="middle").as_role("label")
    doc += svg.paths.star(290, 34, 14, 6)
    return doc


card()

# %% [markdown]
# The same drawing in other built-in themes: `dark`, `print`, `mono` and `brutalist`.

# %%
card("dark")

# %%
card("print")

# %%
card("mono")

# %%
card("brutalist")

# %% [markdown]
# Every theme side by side.

# %%
COLUMNS, GAP, SCALE = 4, 12, 2


def sheet(names: list[str] | None = None) -> svg.Document:
    """One card per theme in a grid, in registration order."""
    names = names or svg.themes.list()
    rows = -(-len(names) // COLUMNS)
    doc = svg.Document(COLUMNS * (WIDTH + GAP) - GAP, rows * (HEIGHT + GAP) - GAP)
    for index, name in enumerate(names):
        x, y = (index % COLUMNS) * (WIDTH + GAP), (index // COLUMNS) * (HEIGHT + GAP)
        doc += svg.Image(card(name).rasterize(scale=SCALE), x, y, WIDTH, HEIGHT)
    return doc


sheet()

# %% [markdown]
# Save the sheet and one file per theme. Next: [19 Custom themes](../19_custom_themes/custom_themes.py).

# %%
if __name__ == "__main__":
    sheet().save("18_themes.svg")
    for name in svg.themes.list():
        card(name).save(f"18_theme_{name}.svg")
