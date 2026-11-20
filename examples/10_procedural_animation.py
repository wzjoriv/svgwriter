"""# Procedural animation

A scene for ``python -m svgwriter animate``. The script defines a drawing (``doc``) and an
``update(doc, seconds)`` function that moves it; the animate command renders one frame per time step.

    python -m svgwriter animate examples/10_procedural_animation.py -o orbit.gif --renderer skia
    python 10_procedural_animation.py                  writes the first frame as SVG
"""

import math
import os
import tempfile
from pathlib import Path

import svgwriter as svg

# %% [markdown]
# The static scene: a sun, an orbit path and a planet. The `FPS`, `DURATION` and `RENDERER`
# constants are read by `svgwriter animate` as defaults.

# %%
SIZE = 160
CENTER = SIZE / 2
ORBIT = 50
FPS = 24
DURATION = 2.0
RENDERER = "skia"

doc = svg.Document(SIZE, SIZE)
glow = doc.radial_gradient(svg.Stop(0, "gold"), svg.Stop(1, "orangered"))
doc.rect(0, 0, SIZE, SIZE, fill="midnightblue")
doc.circle(CENTER, CENTER, ORBIT, fill="none", stroke="slategray", stroke_dasharray=(3, 3))
doc.circle(CENTER, CENTER, 18, fill=glow)
planet = doc.circle(CENTER + ORBIT, CENTER, 7, fill="deepskyblue")
doc

# %% [markdown]
# `update` sets the planet's position for a given time. Calling it with a quarter of the duration
# moves the planet a quarter of the way round.

# %%
def update(doc: svg.Document, seconds: float) -> None:
    angle = 2 * math.pi * seconds / DURATION
    planet.cx = CENTER + ORBIT * math.cos(angle)
    planet.cy = CENTER + ORBIT * math.sin(angle)


update(doc, DURATION / 4)
doc

# %% [markdown]
# Back to the first frame and save it. Set `SVGWRITER_EXAMPLES_OUT` to choose the folder.
# This cell is skipped when `svgwriter animate` loads the script.

# %%
if __name__ == "__main__":
    update(doc, 0)
    out = Path(os.environ.get("SVGWRITER_EXAMPLES_OUT") or tempfile.mkdtemp(prefix="svgwriter-"))
    out.mkdir(parents=True, exist_ok=True)
    doc.save(out / "10_orbit_frame0.svg")
    print("saved 10_orbit_frame0.svg")
