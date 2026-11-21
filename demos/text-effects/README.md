# Text effects

A passage on a night card where five words do what they say: **Smoke** curls, **Metal** shines, **Wind**
blows, **sparks** burn and **Snow** falls.

What it shows:

- `svg.effects` on ranges of a line: `line[start:end].effect("smoke")` styles only those letters,
  and every word stays live, selectable text.
- SMIL animation: the SVG plays in a browser, and the same document renders to a GIF.
- The theme (`theme.toml`), a component (`components/card.py`, the card with its stars) and a project
  animation preset (`animations/twinkle.py`).

```
svgwriter preview    # the animated SVG and the GIF
svgwriter build      # output/text-effects.svg and output/text-effects.gif
```

The GIF renders every frame with filters, so it takes a minute or so; lower `fps` in `svgwriter.toml` for
a quicker draft.
