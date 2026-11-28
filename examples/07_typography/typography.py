"""# Typography

You will build: a type specimen with styled words, wavy letters and a stencil, plus lines in five languages.

Run it from this folder with ``python typography.py``, or open ``typography.ipynb``.
"""

import math

import svgwriter as svg

# %% [markdown]
# Text stays real, selectable text. Slicing it (`title[0:10]`) picks some letters to style differently.

# %%
WIDTH, HEIGHT = 420, 220
SERIF = "Georgia, Times New Roman, serif"
SANS = "Arial, Helvetica, sans-serif"

doc = svg.Document(WIDTH, HEIGHT)
doc.style("text { font-family: Arial, Helvetica, sans-serif; } .accent { fill: #be123c; }")
doc.rect(0, 0, WIDTH, HEIGHT, fill="#fffbeb")

title = doc.text("Typography in SVG", x=20, y=50, font_size=34, font_family=SERIF, fill="#1c1917")
title[0:10].wrap(class_="accent", font_style="italic")
doc

# %% [markdown]
# Each letter can move on its own: here they follow a wave, and the first word tilts.

# %%
wave = doc.text("characters stay text", x=20, y=105, font_size=24, fill="#0f766e")
for index, glyph in enumerate(wave):
    glyph.translate(0, 6 * math.sin(index / 2))
wave[0:10].rotate(-8)
doc

# %% [markdown]
# Subtracting text from a shape cuts the letters out, like a stencil.

# %%
stencil = svg.rect(20, 130, 380, 70, rx=10) - svg.text("STENCIL", x=210, y=187, font_size=56,
                                                      font_family=SANS, font_weight="bold",
                                                      text_anchor="middle")
doc += stencil.update(fill="#1c1917")
doc

# %% [markdown]
# `glyphs()` turns text into one shape per letter, which you can then resize like any shape.

# %%
outlines = svg.text("glyphs", x=330, y=105, font_size=28, font_family=SERIF).glyphs()
for index, path in enumerate(outlines):
    path.update(fill="#7c3aed").scale(1 + index * 0.08)
doc += outlines
doc

# %% [markdown]
# ## Many languages
#
# Hindi, Bengali, Urdu, Japanese and Chinese just work: missing letters are taken from another installed font.
# `xml_lang` picks Japanese or Chinese letter shapes, and `direction="rtl"` writes Urdu right to left.

# %%
LINES = (
    ("Hindi", "नमस्ते दुनिया", {}),
    ("Bengali", "ওহে বিশ্ব, কেমন আছো", {}),
    ("Urdu", "ہیلو دنیا", {"direction": "rtl", "x": 380}),
    ("Japanese", "こんにちは、世界", {"xml_lang": "ja"}),
    ("Chinese", "你好，世界", {"xml_lang": "zh"}),
)
world = svg.Document(WIDTH, 40 + 44 * len(LINES))
world.rect(0, 0, WIDTH, 40 + 44 * len(LINES), fill="#fffbeb")
for row, (name, line, options) in enumerate(LINES):
    baseline = 50 + 44 * row
    world.text(name, x=20, y=baseline, font_size=13, font_family=SANS, fill="#78716c")
    options = {"x": 130, **options}
    world.text(line, y=baseline, font_size=26, font_family=SANS, fill="#1c1917", **options)
world

# %% [markdown]
# ## Font weights and sizes
#
# A `Typeface` is a font family. `measure` tells how wide a word will be, so words can sit side by side,
# and its metrics give the heights of small and capital letters (the lines behind "Hxg").

# %%
sans = svg.Typeface("sans-serif")
faces = svg.Document(WIDTH, 130)
faces.rect(0, 0, WIDTH, 130, fill="#fffbeb")
x = 20
for weight in (300, 400, 700, 900):
    label = f"Aa {weight}"
    faces.text(label, x=x, y=45, font_family=sans, font_size=22, font_weight=weight, fill="#1c1917")
    x += sans.measure(label, 22, weight=weight) + 18
metrics = sans.face(weight=700).metrics.at(44)
for height, color in ((0, "#78716c"), (metrics.x_height, "#0f766e"), (metrics.cap_height, "#be123c")):
    faces.line(20, 110 - height, 400, 110 - height, stroke=color, stroke_width=0.75)
faces.text("Hxg", x=20, y=110, font_family=sans, font_size=44, font_weight=700, fill="#1c1917")
faces

# %% [markdown]
# Save them. Next: [08 Paint](../08_paint/paint.py) fills shapes with gradients and patterns.

# %%
doc.save("07_typography.svg")
doc.save("07_typography.png", scale=2)
world.save("07_scripts.svg")
faces.save("07_typefaces.svg")
