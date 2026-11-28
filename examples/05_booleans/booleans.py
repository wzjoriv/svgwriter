"""# Booleans

You will build: a flower sticker made by merging petals, punching a hole and cutting a letter out of a coin.

Run it from this folder with ``python booleans.py``, or open ``booleans.ipynb``.
"""

import svgwriter as svg

# %% [markdown]
# Six petals, each a turned copy of one ellipse.

# %%
SIZE = 240
CENTER = SIZE / 2
PETALS = 6
FONT = "Arial, Helvetica, sans-serif"

doc = svg.Document(SIZE, SIZE)
doc.rect(0, 0, SIZE, SIZE, fill="ivory")
petal = svg.Ellipse(CENTER, CENTER - 50, 22, 50)
petals = [petal.clone().rotate(360 * i / PETALS, about=(CENTER, CENTER)) for i in range(PETALS)]
doc

# %% [markdown]
# `union` merges shapes into one outline, so the flower has a single clean edge.

# %%
flower = petals[0].union(*petals[1:])
doc += flower.update(fill=svg.LinearGradient.vertical("orchid", "indigo"), stroke="indigo", stroke_width=2)
doc

# %% [markdown]
# Subtracting a shape (`-`) cuts it away: a hole through the middle of the flower.

# %%
flower -= svg.Circle(CENTER, CENTER, 30)
doc

# %% [markdown]
# Text can be cut out too: a gold coin with the letter "A" punched through it.

# %%
letter = svg.Text("A", x=CENTER, y=CENTER + 12, font_size=34, font_family=FONT, font_weight="bold",
                  text_anchor="middle")
doc += (svg.Circle(CENTER, CENTER, 26) - letter).update(fill="gold")
doc

# %% [markdown]
# `stroked(width)` turns an outline into a filled ring, ready for more cutting or merging.

# %%
doc += svg.Circle(CENTER, CENTER, 110).stroked(4).update(fill="indigo")
doc

# %% [markdown]
# Save it. Next: [06 Measuring](../06_measuring/measuring.py) measures paths and finds points on them.

# %%
doc.save("05_booleans.svg")
