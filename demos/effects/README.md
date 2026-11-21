# Effects

A passage on a night card where five words do what they say: **Smoke** curls, **Metal** shines, **Wind**
blows, **sparks** burn and **Snow** falls. Beside it, a logo and two buttons wear the same effects.

What it shows:

- `svg.effects` on ranges of a line: `line[start:end].effect("smoke")` styles only those letters,
  and every word stays live, selectable text.
- `element.effect("metal")` on shapes: the logo and the buttons, each effect sized to the shape's bounding box.
- SMIL animation: the SVG plays in a browser, and the same document renders to a GIF.
- The theme (`theme.toml`), a component (`components/card.py`, the card with its stars) and a project
  animation preset (`animations/twinkle.py`).

Controls (`svgwriter preview` shows them as a form): a dropdown per highlighted word (Smoke, Metal, Wind, sparks, Snow) picks its effect from `svg.effects`, and two more pick the effects of the logo and of the buttons. The defaults give the effects named above.

Open the notebook, [effects.ipynb](effects.ipynb), to see the demo step by step with its pictures; run it to get a panel for the controls.

```
svgwriter preview    # the animated SVG and the GIF
svgwriter build      # output/effects.svg and output/effects.gif
```

The GIF renders every frame with filters, so it takes a minute or so; lower `fps` in `svgwriter.toml` for
a quicker draft.
