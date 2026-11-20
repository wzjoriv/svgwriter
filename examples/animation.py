"""Animation presets: draw-on, morph, stagger, spin and typewriter, saved as SVG and an animated GIF.

Run it as ``python animation.py`` or open ``animation.ipynb``; the SVG animates in the notebook.
"""

import os
import tempfile
from pathlib import Path

import svgwriter as svg

# %% [markdown]
# `element.animate` adds ready-made SMIL animations and chains. `draw` strokes a ring on like a pen.

# %%
WIDTH, HEIGHT = 300, 200
NAVY, GOLD, CORAL, TEAL = "#14213d", "#fca311", "#ff6b6b", "#2ec4b6"

doc = svg.Document(WIDTH, HEIGHT)
doc.rect(0, 0, WIDTH, HEIGHT, rx=16, fill=NAVY)
ring = doc.circle(80, 90, 52, fill="none", stroke=GOLD, stroke_width=6, stroke_linecap="round")
ring.animate.draw(1.2, begin=0.2)
doc

# %% [markdown]
# `morph` turns a `<path>` into any other shape, and `tween` changes any attribute alongside it.

# %%
star = svg.Polygon.regular(80, 90, 34, 5, fill=CORAL).to_path()
doc.add(star)
star.animate.fade_in(0.4, begin=0.8).morph(svg.circle(80, 90, 30), 1.0, begin=1.4).tween("fill", CORAL, TEAL, 1.0, begin=1.4)
doc

# %% [markdown]
# `stagger` applies a preset to each child of a group, each starting a little after the last.

# %%
dots = doc.group()
for index, color in enumerate((CORAL, GOLD, TEAL, "#e5e5e5", "#8ecae6")):
    dots.add(svg.circle(160 + index * 28, 60, 10, fill=color))
dots.animate.stagger("fade_in", step=0.2, dur=0.3, begin=0.6).stagger("grow", step=0.2, dur=0.5, begin=0.6)
doc

# %% [markdown]
# `spin` turns an element about its centre, repeating forever, and `typewriter` reveals text one character at a time.

# %%
spinner = doc.add(svg.Polygon.regular(244, 122, 16, 4, fill=GOLD))
spinner.animate.fade_in(0.4, begin=1.0).spin(2.4, begin=1.0, repeat="indefinite")
caption = doc.text("svgwriter", x=160, y=170, font_size=26, font_family="Arial, Helvetica, sans-serif", font_weight="bold", fill="white")
caption.animate.typewriter(1.2, begin=1.2)
doc

# %% [markdown]
# `doc.at(seconds)` is a still of any moment; here the end of the entrance.

# %%
doc.at(3.0)

# %% [markdown]
# Save the animated SVG and a small animated GIF (`fps`, `duration` and `scale` keep it light).
# Set `SVGWRITER_EXAMPLES_OUT` to choose the folder.

# %%
out = Path(os.environ.get("SVGWRITER_EXAMPLES_OUT") or tempfile.mkdtemp(prefix="svgwriter-"))
out.mkdir(parents=True, exist_ok=True)
doc.save(out / "animation.svg")
doc.save(out / "animation.gif", fps=12, duration=3.6)
print("saved animation.svg and animation.gif")
