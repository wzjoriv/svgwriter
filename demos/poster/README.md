# Poster

*Beach clean-up*: an A4 print poster inviting people to a beach clean-up, drawn in millimetres. `size = "a4"`
makes every coordinate a millimetre, so the PDF prints at true size (210 x 297 mm) and the PNG comes out at
300 dpi.

What it shows:

- Gradients (`sunset`, `ocean`) for the sky and the sea, and the `waves` pattern sized in millimetres.
- A route along the beach (`components/route.py`) with markers at every stop, sized in stroke widths.
- Drawn icons of what to bring in an `HStack` (`components/bring.py`), each on a themed badge, and the
  morning's plan as a `Grid` read from `assets/data/schedule.csv` (`components/schedule.py`).
- `svg.Typeface` for the title and label faces, and the theme with its sizes in millimetres.

Controls (`svgwriter preview` shows them as a form): the colour `theme` (the project's own, `night`, `blueprint` or `mint`), an accent `hue` shift of the theme's primary, secondary and accent colours, and the event's `title`, `date`, `time` and `place`. The defaults give the poster `svgwriter build` writes.

Open the notebook, [poster.ipynb](poster.ipynb), to see the demo step by step with its pictures; run it to get a panel for the controls.

```
svgwriter preview    # the poster as PDF, PNG and SVG
svgwriter build      # output/poster.pdf (A4), output/poster.png (300 dpi) and output/poster.svg
```

The faces are the installed `serif` and `sans-serif` families. To use a font of your own, drop its OFL
`.ttf` or `.otf` files into `assets/fonts/` (registered before every build) and name the family in
`main.py`, for example `svg.Typeface("Fraunces")`.
