"""# Blobs

A website hero banner: a headline, a line of text and a "Get started" button beside gooey metaballs. The
circles drift on closed loops inside one group under `svg.filters.goo`, which blurs the group and sharpens
its edge again, so blobs that come close stretch a bridge, merge, and split apart. The banner is written as a
looping animated SVG (for the page) and a GIF (for previews and social posts).
"""

# %%
from animations import drift
from components import body

import svgwriter as svg

LOOP = 4.0          # seconds before the scene repeats at normal speed
PAD = 64            # left margin of the words
HEADLINE = "Ideas that flow"
TAGLINE = "Sketch, iterate and ship drawings from plain Python."
ACTION = "Get started"
MELT = 14           # how far apart blobs still reach for each other
BLOBS = (           # radius, loop width, loop height, turns, phase; the first is the large one
    (46, 0, 0, 1, 0.0),
    (30, 120, 40, 1, 0.0),
    (26, 110, 50, 1, 3.1),
    (22, 80, 70, 2, 1.6),
    (18, 160, 30, 1, 4.7),
    (24, 140, 60, 1, 1.1),
    (16, 100, 80, 2, 5.4),
    (20, 170, 20, 1, 2.3),
    (14, 60, 90, 1, 3.9),
)

# %% [markdown]
# The `drift` behaviour from `animations/` moves each circle; `self.attach` checks its options. Every
# loop is a whole number of turns in one period, so the GIF and the baked SVG loop seamlessly. A faster
# `speed` shortens the period, so the loop stays seamless at any speed.

# %%
class Blobs(svg.Scene):
    """A hero banner: blobs merging and splitting around a large one, beside a headline and a button."""

    width, height = 960, 400
    fps = 15

    def __init__(self, count: int = 5, melt: float = MELT, speed: float = 1.0, headline: str = HEADLINE,
                 action: str = ACTION) -> None:
        self.count, self.melt = count, melt
        self.headline, self.action = headline, action
        self.duration = LOOP / speed
        super().__init__()

    def build(self, doc: svg.Document) -> None:
        doc.rect(0, 0, self.width, self.height).as_role("background")
        palette = doc.theme.palette
        cx, cy = self.width * 0.72, self.height / 2
        blobs = BLOBS[:self.count]
        circles = [svg.circle(cx, cy, radius) for radius, *_ in blobs]
        doc += body(circles, top=palette["secondary"], bottom=palette["primary"], height=self.height, melt=self.melt)
        for circle, (_, rx, ry, turns, phase) in zip(circles, blobs, strict=True):
            if rx or ry:
                self.attach(circle, drift, rx=rx, ry=ry, turns=turns, phase=phase, period=self.duration)
        glints = doc.group(fill="#ffffff", opacity=0.35)
        glints += svg.circle(cx - 14, cy - 18, 8)
        self.copy(doc)

    def copy(self, doc: svg.Document) -> None:
        """The words on the left: headline, a line of text and the call-to-action button."""
        doc.text(self.headline, x=PAD, y=150, font_size=44, font_weight="bold").as_role("title")
        doc.text(TAGLINE, x=PAD, y=192, font_size=18).as_role("subtitle")
        button = doc.group()
        button.rect(PAD, 228, 168, 52, rx=26).as_role("button")
        button.text(self.action, x=PAD + 84, y=261, font_size=18, font_weight="bold",
                    text_anchor="middle").as_role("button.label")
        button.interact.button()


# %% [markdown]
# The controls: how many blobs, how far they reach for each other (the goo filter's `melt`), how fast they
# move, and the banner's headline and button text. The button dims on hover and flashes when pressed in the
# SVG (`interact.button()`). The function bakes the scene into an animated document, so `svgwriter preview` shows the
# form and plays the result, and `svg.interact` does the same in a notebook.

# %%
@svg.widgets.controls(
    count=svg.widgets.IntSlider(1, len(BLOBS), value=5, label="blobs"),
    melt=svg.widgets.Slider(4, 30, step=1, value=MELT, label="gooeyness"),
    speed=svg.widgets.Slider(0.5, 3, step=0.25, value=1.0),
    headline=svg.widgets.Text(HEADLINE),
    action=svg.widgets.Text(ACTION, label="button"),
)
def blobs(doc: svg.Document, *, count: int = 5, melt: float = MELT, speed: float = 1.0, headline: str = HEADLINE,
          action: str = ACTION) -> svg.Document:
    """The hero banner for these controls, baked into an animated document."""
    return Blobs(count, melt, speed, headline, action).bake()


# %%
if __name__ == "__main__":
    print(*svg.Project.load().build(), sep="\n")
