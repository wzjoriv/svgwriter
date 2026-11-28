# svgwriter

**svgwriter** builds, edits and renders vector graphics in Python with a complete SVG 1.1 object model.
Shapes move, rotate and scale through one transform; geometry has boolean operations and measurement;
text, images and colors are first-class and numpy-backed; documents render with skia and export to PNG,
PDF, TikZ, DXF, G-code, Excalidraw, icons and more.

```python
import svgwriter as svg

doc = svg.Document()
doc.rect(0, 0, 160, 60, rx=12, fill=svg.LinearGradient.horizontal("gold", "tomato"))
title = doc.text("svgwriter", x=88, y=36, font_size=18, text_anchor="middle")
title[3:].fill = "navy"
doc += svg.paths.star(0, 0, 10, fill="navy").place(30, 30).rotate(15)
doc.save("badge.png", scale=3)
```

```{toctree}
:caption: Start
:maxdepth: 1

start/installation
start/quickstart
demos
```

```{toctree}
:caption: Drawing
:maxdepth: 1

guides/geometry
guides/layout
guides/paths
guides/text
guides/fonts
guides/colors-and-images
guides/filters
guides/presets
```

```{toctree}
:caption: Documents & output
:maxdepth: 1

guides/documents
guides/themes
guides/projects
guides/rendering
guides/batches
guides/export
guides/print-and-colour
guides/diagrams-and-office
```

```{toctree}
:caption: Motion
:maxdepth: 1

guides/animation
guides/scenes-and-video
guides/widgets
```

```{toctree}
:caption: More
:maxdepth: 1

guides/units
guides/inkscape
guides/extending
```

```{toctree}
:caption: Explanation
:maxdepth: 1

explanation/design
explanation/conformance
contributing
```

```{toctree}
:caption: Reference
:maxdepth: 2

reference/index
```
