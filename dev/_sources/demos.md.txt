# Demos

The [`demos/`](https://github.com/wzjoriv/svgwriter/tree/main/demos) folder holds complete design projects.
Each one is an ordinary project, as `svgwriter new` makes them: `svgwriter.toml`, `main.py`, `theme.toml`,
`components/`, `animations/` and `assets/`, and each uses several features together. Open a demo's folder
and run `svgwriter preview` to see it live (with its controls, where it has them), or `svgwriter build` to
write its outputs into `output/`. The [`examples/`](https://github.com/wzjoriv/svgwriter/tree/main/examples)
stay short scripts about one topic each; see {doc}`guides/projects` for how projects work.

## Playing card

![An adjustable playing card](_static/demos/playing-card.png)

[`demos/playing-card`](https://github.com/wzjoriv/svgwriter/tree/main/demos/playing-card): a card with
rank and suit buttons, hue, iridescence, glow, corner radius and width controls
(`@svg.widgets.controls`), corner indices, pips and court panels built from layout groups, and a sweep of
the same parameters written as a GIF. Outputs: SVG, PNG, PDF and GIF.

## Calculator kit

![A calculator UI](_static/demos/calculator-kit.png)

[`demos/calculator-kit`](https://github.com/wzjoriv/svgwriter/tree/main/demos/calculator-kit): a calculator
UI from `VStack`, `HStack` and `Grid`, with controls for the shell style, key shape, keypad layout, display
font, size and alignment, history line, key font and weight, spacing and palette. Outputs: SVG, PNG and PDF.

## Text effects

![Words that smoke, shine, blow, burn and snow](_static/demos/text-effects.gif)

[`demos/text-effects`](https://github.com/wzjoriv/svgwriter/tree/main/demos/text-effects): a passage on a
night card where five words carry the smoke, metal, wind, fire and snow effects while staying text.
Outputs: an animated SVG and a GIF.

## Planets explainer

![The eight planets with their orbits to scale](_static/demos/planets-explainer.gif)

[`demos/planets-explainer`](https://github.com/wzjoriv/svgwriter/tree/main/demos/planets-explainer): two
scenes, the eight planets on orbits drawn to scale and Betelgeuse beside the Sun with a rolling counter,
moved by behaviours, SMIL and per-frame updates, then baked. Outputs: MP4 (GIF without ffmpeg), animated
SVG and PowerPoint.

## Blobs

![Gooey blobs merging and splitting](_static/demos/blobs.gif)

[`demos/blobs`](https://github.com/wzjoriv/svgwriter/tree/main/demos/blobs): metaballs that merge and split
under the goo filter, moved by a project behaviour on a seamless loop. Outputs: GIF and animated SVG.

## Poster

![An A4 tide atlas poster](_static/demos/poster.png)

[`demos/poster`](https://github.com/wzjoriv/svgwriter/tree/main/demos/poster): an A4 print poster drawn in
millimetres with typefaces, gradients, patterns, markers, a legend and a tide table. Outputs: a true-size
PDF, a 300 dpi PNG and an SVG.

The pictures on this page are built from the demos by `python scripts/dev.py svgwriter gallery`.
