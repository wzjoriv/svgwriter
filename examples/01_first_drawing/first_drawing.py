"""# Your first drawing

You will build: a little house under a sunny sky, saved as an SVG file.

Run it from this folder with ``python first_drawing.py``, or open ``first_drawing.ipynb``.
"""

import svgwriter as svg

# %% [markdown]
# A `Document` is your canvas. `doc.rect`, `doc.circle` and friends draw a shape and return it.

# %%
WIDTH, HEIGHT = 320, 200
doc = svg.Document(WIDTH, HEIGHT)
doc.rect(0, 0, WIDTH, HEIGHT, fill=svg.LinearGradient.vertical("lightskyblue", "white"))
doc.circle(260, 50, 30, fill="gold")
doc.rect(0, 170, WIDTH, 30, fill="seagreen")
doc

# %% [markdown]
# A group keeps shapes together: everything drawn inside the `with` block shares its outline and position.

# %%
with doc.group(stroke="saddlebrown", stroke_width=2, transform="translate(100 50)"):
    doc.rect(0, 40, 100, 80, fill="wheat")
    doc.polygon([(-10, 40), (50, 0), (110, 40)], fill="firebrick")
    doc.rect(40, 80, 20, 40, fill="sienna")
    doc.rect(12, 56, 16, 16, fill="lightblue")
    doc.rect(72, 56, 16, 16, fill="lightblue")
doc

# %% [markdown]
# Text is a shape too.

# %%
doc.text("Home", x=WIDTH / 2, y=30, text_anchor="middle", font_family="Georgia, serif", font_size=22)
doc

# %% [markdown]
# Save it. Next: [02 Transforms](../02_transforms/transforms.py) turns, flips and moves shapes.

# %%
doc.save("01_first_drawing.svg")
