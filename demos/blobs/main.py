"""# Blobs

Gooey metaballs: circles drift on closed loops inside one group under `svg.filters.goo`, which blurs the
group and sharpens its edge again, so blobs that come close stretch a bridge, merge, and split apart.
"""

# %%
from animations import drift
from components import body

import svgwriter as svg

LOOP = 4.0          # seconds before the scene repeats
MELT = 14           # how far apart blobs still reach for each other
BLOBS = (           # radius, loop width, loop height, turns, phase
    (46, 0, 0, 1, 0.0),
    (30, 120, 40, 1, 0.0),
    (26, 110, 50, 1, 3.1),
    (22, 80, 70, 2, 1.6),
    (18, 160, 30, 1, 4.7),
)

# %% [markdown]
# The `drift` behaviour from `animations/` moves each circle; `self.attach` checks its options. Every
# loop is a whole number of turns in `LOOP` seconds, so the GIF and the baked SVG loop seamlessly.

# %%
class Blobs(svg.Scene):
    """Five blobs merging and splitting around a large one."""

    width, height = 560, 320
    fps = 15
    duration = LOOP

    def build(self, doc: svg.Document) -> None:
        doc.rect(0, 0, self.width, self.height).as_role("background")
        palette = doc.theme.palette
        cx, cy = self.width / 2, self.height / 2
        circles = [svg.circle(cx, cy, radius) for radius, *_ in BLOBS]
        doc += body(circles, top=palette["secondary"], bottom=palette["primary"], height=self.height, melt=MELT)
        for circle, (_, rx, ry, turns, phase) in zip(circles, BLOBS, strict=True):
            if rx or ry:
                self.attach(circle, drift, rx=rx, ry=ry, turns=turns, phase=phase, period=LOOP)
        glints = doc.group(fill="#ffffff", opacity=0.35)
        glints += svg.circle(cx - 14, cy - 18, 8)


# %%
if __name__ == "__main__":
    print(*svg.Project.load().build(), sep="\n")
