"""# Pixels and compositing

numpy pixels sit next to vectors, and Porter-Duff operators combine pixels with shapes, text and other images.

Run it as ``python 06_pixels_and_compositing.py`` or open ``06_pixels_and_compositing.ipynb`` to see each step.
"""


import numpy as np

import svgwriter as svg

# %% [markdown]
# An `Image` takes a numpy array (float 0-1, rows x columns x channels). This one is a generated
# plasma pattern, rotated slightly.

# %%
SIZE = 128
y, x = np.mgrid[0:SIZE, 0:SIZE] / SIZE
value = np.sin(10 * x) + np.sin(10 * y + 2) + np.sin(10 * np.hypot(x - 0.5, y - 0.5))
phase = (value - value.min()) / np.ptp(value)
pixels = np.dstack([phase, 1 - phase, 0.5 + 0.5 * np.sin(6 * phase)])

doc = svg.Document(320, 180)
doc.rect(0, 0, 320, 180, fill="#111827")
picture = svg.Image(pixels, 20, 20, 140, 140)
doc += picture.rotate(-6)
doc

# %% [markdown]
# `picture.alpha` is a second array for transparency: here a soft round fade.

# %%
picture.alpha = np.clip(1.6 - 2.4 * np.hypot(x - 0.5, y - 0.5), 0, 1)
doc

# %% [markdown]
# Vectors sit beside the pixels, and any element can be rasterized back into an `Image` with
# `to_image`, then placed and scaled like one.

# %%
vector = doc.group(stroke="#f9fafb", stroke_width=3, fill="none")
vector.add(svg.circle(240, 90, 50))
vector.add(svg.paths.gear(240, 90, 32, teeth=12, fill="#f59e0b", stroke="none"))
snapshot = vector.to_image(scale=0.5)
doc += snapshot.place(240, 155) * 0.35
doc

# %% [markdown]
# ## Compositing
#
# `image.pixels` holds the data, and pixels combine with the Porter-Duff operators of `feComposite`:
# `a | b` is *a* over *b*, `a & b` keeps *a* where *b* is opaque, `a - b` keeps it where *b* is not,
# `a ^ b` keeps what is not shared and `a * b` is the multiply blend. The other side may be a shape,
# text or a whole document: it is drawn on the pixel grid first (`on_grid`), one user unit per pixel.
# Here one plasma square is masked by a circle (`&`), cut by a star (`-`), and the text drawn on the
# grid goes over it (`|`).

# %%
TILE = 96
tile = svg.Image(pixels[:TILE, :TILE], 0, 0, TILE, TILE).pixels

masked = tile & svg.circle(48, 48, 46)
cut = tile - svg.paths.star(48, 48, 40, points=5)
label = svg.text("pixels", x=48, y=54, font_size=20, font_family="Arial, Helvetica, sans-serif",
                 font_weight="bold", text_anchor="middle", fill="white")
labelled = tile.on_grid(label) | tile

board = svg.Document(4 * TILE + 5 * 12, TILE + 24)
board.rect(0, 0, 4 * TILE + 60, TILE + 24, fill="#111827")
for index, result in enumerate((tile, masked, cut, labelled)):
    board += svg.Image(result.rgba(), 12 + index * (TILE + 12), 12, TILE, TILE)
board

# %% [markdown]
# `composite(backdrop, operator)` takes any operator or blend mode by name, and a `(1, 1, 4)` array is
# a solid color that broadcasts. Multiply tints the tile and screen lightens it.

# %%
amber = np.array([[[1.0, 0.65, 0.2, 1.0]]])
tinted = tile.composite(amber, "multiply")
screened = tile.composite(amber, "screen")
doc2 = svg.Document(2 * TILE + 36, TILE + 24)
doc2.rect(0, 0, 2 * TILE + 36, TILE + 24, fill="#111827")
doc2 += svg.Image(tinted.rgba(), 12, 12, TILE, TILE)
doc2 += svg.Image(screened.rgba(), TILE + 24, 12, TILE, TILE)
doc2

# %% [markdown]
# Save the drawings.

# %%
doc.save("06_pixels.svg")
board.save("06_compositing.svg")
doc2.save("06_blend.svg")
