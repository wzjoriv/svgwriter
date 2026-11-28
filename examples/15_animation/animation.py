"""# Animation

You will build: an animated title card where a ring draws itself, a star morphs into a circle and the
caption types itself out, saved as an animated SVG and a GIF.

Run it from this folder with ``python animation.py``, or open ``animation.ipynb``; the SVG plays in the notebook.
"""

import svgwriter as svg

# %% [markdown]
# `element.animate` adds ready-made animations that play in any browser. `draw` traces a ring like a pen.

# %%
WIDTH, HEIGHT = 300, 200
NAVY, GOLD, CORAL, TEAL = "#14213d", "#fca311", "#ff6b6b", "#2ec4b6"

doc = svg.Document(WIDTH, HEIGHT)
doc.rect(0, 0, WIDTH, HEIGHT, rx=16, fill=NAVY)
ring = doc.circle(80, 90, 52, fill="none", stroke=GOLD, stroke_width=6, stroke_linecap="round")
ring.animate.draw(1.2, begin=0.2)
doc

# %% [markdown]
# Animations chain: the star fades in, `morph`s into a circle and `tween`s its colour at the same time.

# %%
star = svg.Polygon.regular(80, 90, 34, 5, fill=CORAL).to_path()
doc.add(star)
star.animate.fade_in(0.4, begin=0.8).morph(svg.circle(80, 90, 30), 1.0, begin=1.4).tween("fill", CORAL, TEAL, 1.0, begin=1.4)
doc

# %% [markdown]
# `stagger` animates each shape of a group a little after the one before.

# %%
dots = doc.group()
for index, color in enumerate((CORAL, GOLD, TEAL, "#e5e5e5", "#8ecae6")):
    dots.add(svg.circle(160 + index * 28, 60, 10, fill=color))
dots.animate.stagger("fade_in", step=0.2, dur=0.3, begin=0.6).stagger("grow", step=0.2, dur=0.5, begin=0.6)
doc

# %% [markdown]
# `spin` turns a shape forever, and `typewriter` reveals text one letter at a time.

# %%
spinner = doc.add(svg.Polygon.regular(244, 122, 16, 4, fill=GOLD))
spinner.animate.fade_in(0.4, begin=1.0).spin(2.4, begin=1.0, repeat="indefinite")
caption = doc.text("svgwriter", x=160, y=170, font_size=26, font_family="Arial, Helvetica, sans-serif", font_weight="bold", fill="white")
caption.animate.typewriter(1.2, begin=1.2)
doc

# %% [markdown]
# `doc.at(seconds)` is a still picture of any moment: here, after three seconds.

# %%
doc.at(3.0)

# %% [markdown]
# ## Building blocks
#
# For full control, add animation elements to a shape yourself: a blade spins, a dot follows a circle,
# pulses and hides after a while.

# %%
SPEED = 1.0
blocks = svg.Document(200, 200)
blade = blocks.add(svg.Rect(95, 20, 10, 80, rx=5, fill="steelblue"))
blade.append(svg.AnimateTransform.spin(100, 100, dur=SPEED))

track = blocks.define(svg.Path(svg.PathBuilder().circle(100, 100, 70)))
dot = blocks.add(svg.Circle(0, 0, 8, fill="tomato"))
dot.append(svg.AnimateMotion(svg.MPath(track), dur=SPEED * 2, repeat_count=float("inf")))
dot.append(svg.Animate(attribute_name="r", values=[6, 10, 6], dur=1, repeat_count=float("inf")))
dot.append(svg.Set("visibility", "hidden", begin=SPEED * 4, fill=svg.AnimationFill.FREEZE))
blocks

# %% [markdown]
# Save the animated SVG and a small GIF (`fps` and `duration` keep it light).
# Next: [16 Scenes](../16_scenes/scenes.py) moves shapes frame by frame from Python.

# %%
doc.save("15_animation.svg")
doc.save("15_animation.gif", fps=12, duration=3.6)
blocks.save("15_blocks.svg")
