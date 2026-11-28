# Blobs

A website hero banner: a headline, a line of text and a "Get started" button beside gooey metaballs that
drift, stretch bridges when they come close, merge and split apart again, on a seamless four-second loop.
The SVG goes on the page (it loops by itself, and the button dims on hover and flashes when pressed); the GIF
is for previews and social posts.

What it shows:

- `svg.filters.goo` on a group: it blurs the circles together and sharpens the edge again.
- A project behaviour (`animations/drift.py`, `@svg.preset.behavior`) attached with `self.attach`, which
  checks its options; each loop is a whole number of turns, so the animation repeats without a seam.
- A shared gradient in page units (`components/body.py`), so every blob keeps its colour as it moves.
- Baking: the SVG output turns the Python motion into SMIL and plays in a browser like the GIF.
- `button.interact.button()`: the call-to-action responds to the pointer without any script.

Controls (`svgwriter preview` shows them as a form): the number of blobs, how far they reach for each other (`gooeyness`, the goo filter's melt) the `speed` of the loop, and the `headline` and `button` text. The defaults give the five-blob, four-second loop.

Open the notebook, [blobs.ipynb](blobs.ipynb), to see the demo step by step with its pictures; run it to get a panel for the controls.

```
svgwriter preview    # the GIF and the animated SVG
svgwriter build      # output/blobs.gif and output/blobs.svg
```
