# Blobs

Gooey metaballs: five circles drift around a large one, stretch bridges when they come close, merge and
split apart again, on a seamless four-second loop.

What it shows:

- `svg.filters.goo` on a group: it blurs the circles together and sharpens the edge again.
- A project behaviour (`animations/drift.py`, `@svg.preset.behavior`) attached with `self.attach`, which
  checks its options; each loop is a whole number of turns, so the animation repeats without a seam.
- A shared gradient in page units (`components/body.py`), so every blob keeps its colour as it moves.
- Baking: the SVG output turns the Python motion into SMIL and plays in a browser like the GIF.

```
svgwriter preview    # the GIF and the animated SVG
svgwriter build      # output/blobs.gif and output/blobs.svg
```
