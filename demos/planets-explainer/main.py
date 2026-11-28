"""# Planets lesson

A four-slide classroom lesson on the Solar System, written as `Scene` classes: a title slide with the lesson's
goals, "Eight planets" (the orbits to scale while each planet circles the Sun), "700× wider" (the Sun beside
Betelgeuse with a row of 100 Suns counted up) and a quiz whose answers appear when their question is clicked.
The PowerPoint deck has one slide per scene, its animations as slide effects and the quiz answers on click
triggers; the video and the animated SVGs show the same slides.
"""

# %%
import shutil

from animations import orbit
from components import Counter, heading, read_planets

import svgwriter as svg

MARGIN = 80
SUN = (90, 470)            # where the Sun sits in "Eight planets"
AU = 36                    # pixels per astronomical unit
WIDER = 700                # Betelgeuse's diameter in Suns
ROW = 100                  # Suns counted in the row
LABELLED = 2               # orbits beyond this many AU get a name; the inner four share one

# %% [markdown]
# ## Title slide
# The lesson's name and what students will learn, each goal fading in after the last.

# %%
GOALS = ("How far the planets are from the Sun", "How big the Sun is next to another star",
         "Why scale models help us compare")


class Lesson(svg.Scene):
    """The title slide: the lesson's name and its goals."""

    size = "video-720p"
    fps = 30
    duration = 4.0

    def __init__(self, speed: float = 1.0) -> None:
        self.speed = speed
        super().__init__()

    def build(self, doc: svg.Document) -> None:
        doc.rect(0, 0, self.width, self.height).as_role("background")
        title = heading("The Solar System", "Science, lesson 4: distances and sizes", x=MARGIN, y=MARGIN + 80)
        doc += title
        title.animate.fade_in(0.8)
        doc.text("Today we will learn", x=MARGIN, y=MARGIN + 260, font_size=36).as_role("subtitle")
        for index, goal in enumerate(GOALS):
            line = doc.text(f"•  {goal}", x=MARGIN + 20, y=MARGIN + 330 + index * 64, font_size=32).as_role("text")
            line.animate.fade_in(0.6, begin=(0.8 + index * 0.6) / self.speed)


# %% [markdown]
# ## Eight planets
# The orbits are circles about the Sun with radii in AU, so Neptune's is 78 times Mercury's. Planet sizes
# are not to scale (they would be specks). `self.attach` runs the `orbit` behaviour on every planet.

# %%
class Planets(svg.Scene):
    """The orbits to scale, the planets moving on them."""

    size = "video-720p"
    fps = 30
    duration = 6.0

    def __init__(self, speed: float = 1.0) -> None:
        self.speed = speed
        super().__init__()

    def build(self, doc: svg.Document) -> None:
        doc.rect(0, 0, self.width, self.height).as_role("background")
        title = heading("Eight planets", f"Orbit distances to scale: 1 AU = {AU} px", x=MARGIN, y=MARGIN)
        doc += title
        title.animate.fade_in(0.8)
        sun_x, sun_y = SUN
        orbits = doc.group()
        bodies = doc.group()
        for index, planet in enumerate(read_planets()):
            radius = planet.au * AU
            orbits += svg.circle(sun_x, sun_y, radius).as_role("orbit")
            body = svg.circle(sun_x + radius, sun_y, planet.radius, fill=planet.color)
            bodies += body
            self.attach(body, orbit, cx=sun_x, cy=sun_y, au=planet.au, speed=self.speed)
            if planet.au > LABELLED:
                doc.text(planet.name, x=sun_x + radius, y=sun_y + 44 + index % 2 * 26,
                         text_anchor="middle").as_role("caption")
        orbits.animate.stagger("fade_in", step=0.15, dur=0.6, begin=0.4)
        doc.circle(sun_x, sun_y, 9).as_role("shape").filter = svg.filters.glow(6, color="#ffd166")
        doc.text("Mercury to Mars", x=sun_x, y=sun_y - 70, text_anchor="middle").as_role("caption")



# %% [markdown]
# ## 700× wider
# Betelgeuse is about 700 times wider than the Sun. At this scale the Sun is a 2-pixel dot; `update`
# lines up 100 of them while the counter rolls to 100. Seven such rows would span the star.

# %%
class Betelgeuse(svg.Scene):
    """The Sun beside Betelgeuse, and a row of Suns counted up."""

    size = "video-720p"
    fps = 30
    duration = 6.0

    def __init__(self, speed: float = 1.0) -> None:
        self.speed = speed
        super().__init__()

    def build(self, doc: svg.Document) -> None:
        doc.rect(0, 0, self.width, self.height).as_role("background")
        title = heading("700× wider", "Betelgeuse beside the Sun, to scale", x=MARGIN, y=MARGIN)
        doc += title
        title.animate.fade_in(0.8)
        sun = 1.0
        radius = sun * WIDER
        star = doc.circle(self.width / 2, self.height + radius - 260, radius, fill=svg.gradients.blend(
            "#ffb36b", "#ef6f3c", "#7a1f12", angle=90))
        star.filter = svg.filters.glow(24, color="#ef6f3c", opacity=0.6)
        star.animate.breathe(amount=0.01, period=3)
        star.animate.fade_in(1.2, begin=0.3)
        self.row_y = self.height - 300
        self.row_x = self.width / 2 - ROW * sun
        self.suns = doc.group()
        self.suns.as_role("shape")
        self.counter = Counter(doc, x=self.width - MARGIN - 3 * 40, y=MARGIN + 60, places=3, size=64)
        doc.text(f"a row of {ROW} Suns", x=self.width / 2, y=self.row_y - 24,
                 text_anchor="middle").as_role("caption")
        doc.text("Suns in a row", x=self.width - MARGIN, y=MARGIN + 110, text_anchor="end").as_role("caption")

    def update(self, seconds: float) -> None:
        counted = min(max((seconds * self.speed - 1.5) / 3.0, 0.0), 1.0) * ROW
        while len(self.suns.children) < int(counted):
            index = len(self.suns.children)
            self.suns += svg.circle(self.row_x + 2 * index + 1, self.row_y, 1)
        self.counter.show(counted)


# %% [markdown]
# ## Quiz
# Three questions on cards. Each answer starts hidden and fades in when its card is clicked
# (`animate.on("click", card)`): in a browser, and as a click trigger in PowerPoint.

# %%
QUESTIONS = (("Which planet is farthest from the Sun?", "Neptune, about 30 AU away"),
             ("How many Suns would fit across Betelgeuse?", "About 700"),
             ("Why are the planets drawn bigger than they are?", "At true size they would be invisible specks"))


class Quiz(svg.Scene):
    """Check your understanding: click a question to show its answer."""

    size = "video-720p"
    fps = 30
    duration = 1.0

    def __init__(self, speed: float = 1.0) -> None:
        self.speed = speed
        super().__init__()

    def build(self, doc: svg.Document) -> None:
        doc.rect(0, 0, self.width, self.height).as_role("background")
        doc += heading("Check your understanding", "Click a question to reveal its answer", x=MARGIN, y=MARGIN)
        for index, (question, answer) in enumerate(QUESTIONS):
            top = MARGIN + 170 + index * 150
            card = doc.group()
            card.rect(MARGIN, top, self.width - 2 * MARGIN, 120, rx=16).as_role("card")
            card.text(question, x=MARGIN + 32, y=top + 50, font_size=30).as_role("text")
            card.interact.hover(opacity=0.9)
            reveal = doc.text(answer, x=MARGIN + 32, y=top + 96, font_size=28, opacity=0).as_role("answer")
            reveal.animate.on("click", card).fade_in(0.4)


# %% [markdown]
# `scenes` is the project's entry: one slide (and clip) each. Two controls, a time scale and which clip, drive the same
# scenes through a function that bakes the chosen one, which `svg.explore` shows in a notebook.

# %%
scenes = [Lesson, Planets, Betelgeuse, Quiz]
CLIPS = {"Title": Lesson, "Eight planets": Planets, "700× wider": Betelgeuse, "Quiz": Quiz}


@svg.widgets.controls(
    scene=svg.widgets.Segmented(list(CLIPS), value="Eight planets"),
    speed=svg.widgets.Slider(0.25, 4, step=0.25, value=1.0, label="time scale"),
)
def explainer(doc: svg.Document, *, scene: str = "Eight planets", speed: float = 1.0) -> svg.Document:
    """The chosen clip with its clock running *speed* times as fast, baked into an animated document."""
    return CLIPS[scene](speed).bake()

# %%
if __name__ == "__main__":
    project = svg.Project.load()
    formats = ["mp4" if shutil.which("ffmpeg") else "gif", "svg", "pptx"]
    print(*project.build(formats), sep="\n")
