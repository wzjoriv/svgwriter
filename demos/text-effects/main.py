"""# Text effects

A passage on a night card where five words carry their meaning: smoke curls, metal shines, wind blows,
sparks burn and snow falls. Each effect styles a range of the text, so the words stay real, selectable
text, and every effect animates with SMIL.
"""

# %%
from animations import twinkle
from components import card

import svgwriter as svg

LINES = (
    "...into the cold night, and Smoke curled around",
    "his Metal scales. A bitter Wind carried sparks",
    "across the Snow plains, where an...",
)
EFFECT_NAMES = list(svg.effects.__all__)
WORDS = {"Smoke": "smoke", "Metal": "metal", "Wind": "wind", "sparks": "fire", "Snow": "snow"}
"""The starting effect of each word, by name from ``svg.effects``."""
INSET = 16          # card edge to page edge
LEFT = 64           # first letter of each line
FIRST = 108         # baseline of the first line
LEADING = 54        # baseline to baseline

# %% [markdown]
# `line[start:end].effect(name)` moves that range of a line onto a copy just above it, so the effect's
# filter reaches only those letters while the line keeps its spacing. Each word has a dropdown, so
# `svgwriter preview` (or `svg.interact` in a notebook) can swap its effect.

# %%
def effect_choice(word: str) -> svg.widgets.Dropdown:
    """The dropdown that picks the effect of *word*."""
    return svg.widgets.Dropdown(EFFECT_NAMES, value=WORDS[word], label=word)


@svg.widgets.controls(smoke=effect_choice("Smoke"), metal=effect_choice("Metal"), wind=effect_choice("Wind"),
                      sparks=effect_choice("sparks"), snow=effect_choice("Snow"))
def passage(doc: svg.Document, *, smoke: str = "smoke", metal: str = "metal", wind: str = "wind",
            sparks: str = "fire", snow: str = "snow") -> svg.Document:
    """Draw the card and the passage, with the chosen effect on each of the five words."""
    box = doc.root.get("viewBox")
    sky = card(box.width, box.height, inset=INSET, caption="svg.effects")
    doc += sky
    sky.children[2].animate.apply(twinkle)
    effects = {"Smoke": smoke, "Metal": metal, "Wind": wind, "sparks": sparks, "Snow": snow}
    for row, words in enumerate(LINES):
        line = doc.text(words, x=LEFT, y=FIRST + row * LEADING).as_role("text")
        for word, effect in effects.items():
            if word in words:
                start = words.index(word)
                line[start:start + len(word)].effect(effect)
    return doc


# %%
if __name__ == "__main__":
    print(*svg.Project.load().build(), sep="\n")
