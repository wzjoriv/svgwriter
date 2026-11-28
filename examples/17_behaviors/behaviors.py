"""# Behaviors

You will build: a workshop of turning gears, a wobbling sign and a counter, written once in Python and saved
as an SVG that plays in any browser.

Run it from this folder with ``python behaviors.py``, or open ``behaviors.ipynb``.
"""

import svgwriter as svg

# %% [markdown]
# A behavior is a function that sets up a shape for a given time. `@svg.preset.behavior` gives it a name,
# so any shape can use it as `shape.animate.turn()`. `element.home` is the shape as it started.

# %%
INK = "#1f2937"
PAPER = "#f8fafc"
STEEL = "#64748b"
BRASS = "#d97706"


@svg.preset.behavior
def turn(element: svg.Element, seconds: float, *, speed: float = 90.0) -> None:
    """Turn about the anchor at *speed* degrees per second."""
    element.matrix = element.home.matrix
    element.rotate(speed * seconds)


# %% [markdown]
# The scene gives each shape its behavior in `build`: the gears turn, and the sign uses the built-in
# `wiggle`. `update` still runs on every frame for anything else, here the counter.

# %%
class Workshop(svg.Scene):
    width, height, fps, duration = 320, 180, 24, 2.0

    def build(self, doc: svg.Document) -> None:
        doc.rect(0, 0, self.width, self.height, fill=PAPER)
        big = doc.add(svg.paths.gear(110, 90, 50, fill=STEEL))
        big.animate.turn(speed=90)
        small = doc.add(svg.paths.gear(185, 72, 28, fill=STEEL))
        small.animate.turn(speed=-160)
        sign = doc.rect(244, 40, 32, 32, rx=6, fill=BRASS)
        sign.animate.wiggle(angle=12, period=0.4)
        self.counter = doc.text("0", x=260, y=140, font_size=28, fill=INK, text_anchor="middle")

    def update(self, seconds: float) -> None:
        self.counter.children[0] = str(int(seconds * 4))


workshop = Workshop()
workshop.render(0.5)
workshop

# %% [markdown]
# `bake()` turns the Python motion into animation a browser can play on its own, and saving the scene
# as `.svg` or `.pptx` does the same. Next: [18 Themes](../18_themes/themes.py).

# %%
baked = workshop.bake()
baked.at(1.0)

# %%
if __name__ == "__main__":
    workshop.save("17_workshop.svg")
    workshop.save("17_workshop.pptx")
