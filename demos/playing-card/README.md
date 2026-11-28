# Playing card

An adjustable playing card: rank and suit on rows of buttons, the hue, the iridescence, the glow, the corner
radius and the card width on sliders and a toggle.

What it shows:

- `@svg.widgets.controls` on a page function: `svgwriter preview` shows the controls as a form and redraws
  the card as they move; `svgwriter build` uses their starting values.
- Layout groups: the corner indices are `VStack`s, the pips are columns of `VStack`s in an `HStack`, and the
  court panel is a `VStack` with a background, so every part follows the card width.
- `svg.gradients.iridescent` and `svg.filters.glow`, the theme (felt, card stock and suit inks in
  `theme.toml`) and a project animation preset (`animations/deal.py`).
- `svg.sweep`: the same function stepped over time, written as a GIF and an animated SVG.

Controls: rank, suit, hue, iridescence, glow, corner radius and card width (see above); the notebook adds `svg.explore` and stills of other cards.

Open the notebook, [playing-card.ipynb](playing-card.ipynb), to see the demo step by step with its pictures; run it to get a panel for the controls.

```
svgwriter preview    # the card with its controls, live
svgwriter build      # output/playing-card.{svg,png,pdf,gif} and output/playing-card-sweep.{svg,gif,...}
```
