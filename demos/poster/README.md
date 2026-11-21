# Poster

*Tide atlas*: an A4 print poster drawn in millimetres. `size = "a4"` makes every coordinate a
millimetre, so the PDF prints at true size (210 x 297 mm) and the PNG comes out at 300 dpi.

What it shows:

- Gradients (`sunset`, `ocean`) for the sky and the sea, and patterns (`waves`, `dots`, `crosshatch`,
  `hatch`, `zigzag`) sized in millimetres.
- Markers on the route (`components/route.py`): dots at every station and an arrow at the end, sized in
  stroke widths.
- `svg.Typeface` for the title and label faces, layout groups for the legend (`HStack`) and the tide table
  (`Grid`, read from `assets/data/tides.csv`), and the theme with its sizes in millimetres.

Controls (`svgwriter preview` shows them as a form): the colour `theme` (the project's own, `night`, `blueprint` or `mint`), an accent `hue` shift of the theme's primary, secondary and accent colours, and the `title` text. The defaults give the poster `svgwriter build` writes.

Open the notebook, [poster.ipynb](poster.ipynb), to see the demo step by step with its pictures; run it to get a panel for the controls.

```
svgwriter preview    # the poster as PDF, PNG and SVG
svgwriter build      # output/poster.pdf (A4), output/poster.png (300 dpi) and output/poster.svg
```

The faces are the installed `serif` and `sans-serif` families. To use a font of your own, drop its OFL
`.ttf` or `.otf` files into `assets/fonts/` (registered before every build) and name the family in
`main.py`, for example `svg.Typeface("Fraunces")`.
