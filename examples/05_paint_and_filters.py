"""Step 5: paint and filters: gradients, patterns, clip paths, masks, then filter primitives.

Run it as ``python 05_paint_and_filters.py`` or open ``05_paint_and_filters.ipynb`` to see each step.
"""

import os
import tempfile
from pathlib import Path

import svgwriter as svg
from svgwriter.elements import filters as fe

# %% [markdown]
# Paint servers are values you pass as `fill` or `stroke`. A gradient takes `Stop`s along its axis;
# a `Pattern` repeats a tile of graphics.

# %%
PAINT_W, PAINT_H = 400, 200
paint = svg.Document(PAINT_W, PAINT_H)
paint.rect(0, 0, PAINT_W, PAINT_H, fill="#0f172a")

sunset = svg.LinearGradient(svg.Stop(0, "#fde047"), svg.Stop(0.5, "#fb7185"), svg.Stop(1, "#7c3aed"), x1=0, y1=0, x2=1, y2=0)
orb = paint.radial_gradient(svg.Stop(0, "white"), svg.Stop(1, "#38bdf8"), cx=0.4, cy=0.35, r=0.7)
dots = paint.define(svg.Pattern(svg.circle(5, 5, 2.5, fill="#f8fafc"), width=10, height=10, pattern_units="userSpaceOnUse"))

paint.rect(20, 20, 170, 70, rx=10, fill=sunset)
paint.circle(75, 145, 38, fill=orb)
paint.rect(210, 20, 170, 70, rx=10, fill=dots, stroke="#f8fafc", stroke_width=2)
paint

# %% [markdown]
# A `ClipPath` keeps only what lies inside its shapes: a stripe pattern clipped to a star.

# %%
stripes = paint.define(svg.Pattern(svg.rect(0, 0, 6, 12, fill="#fb7185"), width=12, height=12, pattern_units="userSpaceOnUse"))
star_clip = paint.define(svg.ClipPath(svg.builder.star(300, 145, 45, points=5)))
paint.add(svg.Rect(250, 100, 100, 90, fill=stripes, clip_path=star_clip))
paint

# %% [markdown]
# A `Mask` uses the luminance of its content as opacity: white keeps, black hides, grey is in between.
# A gradient mask fades a circle out toward its right edge.

# %%
fade = svg.LinearGradient(svg.Stop(0, "white"), svg.Stop(1, "black"), x1=0, y1=0, x2=1, y2=0)
veil = paint.define(svg.Mask(svg.Rect(130, 100, 90, 90, fill=fade), x=130, y=100, width=90, height=90, mask_units="userSpaceOnUse"))
paint.add(svg.Circle(175, 145, 40, fill="#34d399", mask=veil))
paint

# %% [markdown]
# Filters are defined once with `doc.define(...)` and referenced by shapes through `filter=`.
# Primitives chain: turbulence noise, desaturated by a color matrix, makes a paper texture.

# %%
SIZE = 400
TILE = 160

doc = svg.Document(SIZE, SIZE)
noise = fe.FeTurbulence(0.04, 4, seed=7, type=fe.TurbulenceType.FRACTAL_NOISE)
paper = doc.define(svg.Filter(noise, fe.FeColorMatrix.saturate(0), x=0, y=0, width="100%", height="100%"))
doc.add(svg.Rect(0, 0, SIZE, SIZE, filter=paper))
doc

# %% [markdown]
# `svg.drop_shadow` is a ready-made filter for a soft shadow.

# %%
shadow = doc.define(svg.drop_shadow(4, 4, 3, "black", 0.5))
doc.add(svg.Rect(20, 20, TILE, TILE, rx=16, fill="teal", filter=shadow))
doc

# %% [markdown]
# Lighting: blur the alpha into a bump map, light it with a point light, clip the highlight to the
# shape and add it back onto the source graphic.

# %%
bump = fe.FeGaussianBlur(4, in_=fe.StandardInput.SOURCE_ALPHA)
light = fe.FeSpecularLighting(
    fe.FePointLight(-50, -100, 200),
    in_=bump,
    surface_scale=5,
    specular_constant=0.8,
    specular_exponent=20,
    lighting_color="white",
)
clipped = fe.FeComposite(fe.CompositeOperator.IN, in_=light, in2=fe.StandardInput.SOURCE_ALPHA)
shine = fe.FeComposite(fe.CompositeOperator.ARITHMETIC, in_=fe.StandardInput.SOURCE_GRAPHIC, in2=clipped, k1=0, k2=1, k3=1, k4=0)
embossed = doc.define(svg.Filter(bump, light, clipped, shine))
doc.add(svg.Circle(300, 100, 70, fill="darkorange", filter=embossed))
doc

# %% [markdown]
# A color matrix on text: `FeColorMatrix.grayscale()` removes the purple.

# %%
grey = doc.define(svg.Filter(fe.FeColorMatrix.grayscale()))
doc.add(svg.Text("grey", x=100, y=300, font_size=64, fill="purple", filter=grey))
doc

# %% [markdown]
# Save both, the second with an XML doctype. Set `SVGWRITER_EXAMPLES_OUT` to choose the folder.

# %%
out = Path(os.environ.get("SVGWRITER_EXAMPLES_OUT") or tempfile.mkdtemp(prefix="svgwriter-"))
out.mkdir(parents=True, exist_ok=True)
paint.save(out / "05_paint.svg")
doc.save(out / "05_filters.svg", doctype=True)
print("saved 05_paint.svg and 05_filters.svg")
