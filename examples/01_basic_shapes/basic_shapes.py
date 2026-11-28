"""# Basic shapes

Shapes, gradients, text and nested groups, created with document shortcuts.

Run it as ``python basic_shapes.py`` or open ``basic_shapes.ipynb`` to see each step.
"""


import svgwriter as svg

# %% [markdown]
# A `Document` has shortcuts (`rect`, `circle`, `text`, ...) that create a shape, add it and return it.
# Gradients are values you pass as `fill`.

# %%
WIDTH, HEIGHT = 320, 200
doc = svg.Document(WIDTH, HEIGHT)
doc.title("Basic shapes")
sky = svg.LinearGradient.vertical("lightskyblue", "white")
sun = doc.radial_gradient(svg.Stop(0, "gold"), svg.Stop(1, "orange"), cx=0.5, cy=0.5, r=0.5)

doc.rect(0, 0, WIDTH, HEIGHT, fill=sky)
doc.circle(260, 50, 30, fill=sun)
doc

# %% [markdown]
# `doc.group(...)` is a context manager: shapes added inside share its style and transform,
# and groups nest.

# %%
with doc.group(id="house", stroke="saddlebrown", stroke_width=2, transform="translate(40 80)") as house:
    doc.rect(0, 40, 100, 80, fill="wheat")
    doc.polygon([(-10, 40), (50, 0), (110, 40)], fill="firebrick")
    doc.rect(40, 80, 20, 40, fill="sienna")
    with house.group(fill="lightblue"):
        doc.rect(12, 56, 16, 16)
        doc.rect(72, 56, 16, 16)
doc

# %% [markdown]
# Standalone shapes (`svg.ellipse`, `svg.line`) are added with `+=`. Text takes styled `span`s.

# %%
doc += [
    svg.ellipse(230, 180, 60, 10, fill="seagreen", opacity=0.6),
    svg.line(0, 199, WIDTH, 199, stroke="darkgreen", stroke_width=2),
]
title = doc.text("Home", x=WIDTH / 2, y=24, text_anchor="middle", font_family="sans-serif", font_size=18)
title.span(" sweet home", font_style="italic")
doc

# %% [markdown]
# Save it.

# %%
doc.save("01_basic_shapes.svg")
