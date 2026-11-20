"""# Typography

Text stays live characters: styled ranges, per-glyph moves and rotations, outlines and cut-outs, and lines
in Hindi, Bengali, Urdu, Japanese and Chinese.

Run it as ``python 04_typography.py`` or open ``04_typography.ipynb`` to see each step.
"""

import math
import os
import tempfile
from pathlib import Path

import svgwriter as svg

# %% [markdown]
# Text stays text. Slicing a `Text` selects a character range that can be wrapped in a styled `<tspan>`.

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
# Iterating a `Text` yields its characters, so each can move on its own; a slice rotates as a group.

# %%
wave = doc.text("characters stay text", x=20, y=105, font_size=24, fill="#0f766e")
for index, glyph in enumerate(wave):
    glyph.translate(0, 6 * math.sin(index / 2))
wave[0:10].rotate(-8)
doc

# %% [markdown]
# Subtracting text from a shape cuts the letters out of it, as a stencil.

# %%
stencil = svg.rect(20, 130, 380, 70, rx=10) - svg.text("STENCIL", x=210, y=187, font_size=56,
                                                      font_family=SANS, font_weight="bold",
                                                      text_anchor="middle")
doc += stencil.update(fill="#1c1917")
doc

# %% [markdown]
# `glyphs()` converts text to one outline path per character, which then scale like any shape.

# %%
outlines = svg.text("glyphs", x=330, y=105, font_size=28, font_family=SERIF).glyphs()
for index, path in enumerate(outlines):
    path.update(fill="#7c3aed").scale(1 + index * 0.08)
doc += outlines
doc

# %% [markdown]
# ## World scripts
#
# Scripts that need shaping (Devanagari, Bengali, Arabic) and CJK text work with any `font_family`: where the
# font has no glyph, layout falls back per character to an installed font that has one. `xml_lang` steers
# the choice for shared CJK characters, and `direction="rtl"` with `text_anchor="end"` sets Urdu from the right.

# %%
LINES = (
    ("Hindi", "नमस्ते दुनिया", {}),
    ("Bengali", "ওহে বিশ্ব, কেমন আছো", {}),
    ("Urdu", "ہیلو دنیا", {"direction": "rtl", "text_anchor": "end", "x": 380}),
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
# Save SVG and a 2x PNG. Set `SVGWRITER_EXAMPLES_OUT` to choose the folder.

# %%
out = Path(os.environ.get("SVGWRITER_EXAMPLES_OUT") or tempfile.mkdtemp(prefix="svgwriter-"))
out.mkdir(parents=True, exist_ok=True)
doc.save(out / "04_typography.svg")
doc.save(out / "04_typography.png", scale=2)
world.save(out / "04_scripts.svg")
print("saved 04_typography.svg, .png and 04_scripts.svg")
