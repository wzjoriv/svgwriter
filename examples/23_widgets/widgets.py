"""# Widgets

You will build: a playing card with buttons for rank and suit, sliders for colour and corners and a glow
switch, plus a still per suit and an animation that sweeps through the settings.

Run it from this folder with ``python widgets.py``, or open ``widgets.ipynb`` to use the controls.
"""

import svgwriter as svg

# %% [markdown]
# The card is an ordinary function. `@svg.widgets.controls` names a control for each setting: buttons
# (`Segmented`), `Slider`s and a `Toggle`. Calling the function directly still works.

# %%
SUITS = {"♠": "#1f2937", "♥": "#dc2626", "♦": "#dc2626", "♣": "#1f2937"}
WIDTH, HEIGHT, MARGIN = 150, 210, 12


@svg.widgets.controls(
    rank=svg.widgets.Segmented(["A", "K", "Q", "J"]),
    suit=svg.widgets.Segmented(list(SUITS)),
    hue=svg.widgets.Slider(0, 360, step=1, format="{:.0f}°"),
    radius=svg.widgets.Slider(0, 24, step=0.5, label="corner radius"),
    glow=svg.widgets.Toggle(label="glow"),
)
def card(rank: str = "A", suit: str = "♠", hue: float = 220, radius: float = 12, glow: bool = False) -> svg.Document:
    """A playing card on a tinted face with a border in *hue*."""
    doc = svg.Document(WIDTH + 2 * MARGIN, HEIGHT + 2 * MARGIN)
    accent = svg.Color.from_hsl(hue, 0.7, 0.45)
    face = doc.rect(MARGIN, MARGIN, WIDTH, HEIGHT, rx=radius, fill=svg.Color.from_hsl(hue, 0.6, 0.96),
                    stroke=accent, stroke_width=3)
    if glow:
        face.filter = svg.filters.glow(6)
    doc.rect(MARGIN + 8, MARGIN + 8, WIDTH - 16, HEIGHT - 16, rx=max(radius - 6, 0), fill="none",
             stroke=accent, stroke_width=1, stroke_dasharray="4 3")
    ink = SUITS[suit]
    centre_x, centre_y = MARGIN + WIDTH / 2, MARGIN + HEIGHT / 2
    doc.text(suit, x=centre_x, y=centre_y + 26, font_size=76, text_anchor="middle", fill=ink)
    for turn in (0, 180):
        with doc.group(transform=f"rotate({turn} {centre_x} {centre_y})", fill=ink, text_anchor="middle"):
            doc.text(rank, x=MARGIN + 20, y=MARGIN + 30, font_size=22, font_weight="bold")
            doc.text(suit, x=MARGIN + 20, y=MARGIN + 50, font_size=18)
    return doc


card(rank="Q", suit="♥", hue=330, glow=True).save("23_card.svg")
card()

# %% [markdown]
# In a notebook, `svg.explore(card)` shows the controls beside the card (`pip install "pysvgwriter[widget]"`).
# `.code()` gives the call for the current settings, to paste into a script.

# %%
view = svg.explore(card)
view.update(rank="K", suit="♦", hue=40, radius=4)
view.code()

# %% [markdown]
# One still per suit: the controls are only parameters, so the states are plain calls.

# %%
step = WIDTH + 2 * MARGIN
suits = svg.Document(len(SUITS) * step, HEIGHT + 2 * MARGIN)
for index, (rank, suit, hue) in enumerate(zip("AKQJ", SUITS, (220, 350, 30, 140), strict=True)):
    face = card(rank=rank, suit=suit, hue=hue, radius=6 * index).root
    face.x = index * step
    suits += face
suits.save("23_suits.svg")
suits

# %% [markdown]
# `svg.sweep` turns settings into an animation: a `(start, end)` pair glides, a list steps through its values.
# It saves as an animated SVG or a GIF. Next: [24 Presets](../24_presets/presets.py).

# %%
sweep = svg.sweep(card, hue=(0, 360), radius=(0, 24), suit=list(SUITS), dur=4, fps=12, ease="ease-in-out")
sweep.save("23_card_sweep.svg")
sweep.save("23_card_sweep.gif")
sweep
