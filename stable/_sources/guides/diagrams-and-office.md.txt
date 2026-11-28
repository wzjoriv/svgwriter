# Diagrams and Office files

Diagram languages come in through their own tools, and PowerPoint, Word and Excel files go both ways.
Saving and the other formats are in [Export and import](export.md).

## Diagrams

Graphviz (`.dot`, `.gv`) and Mermaid (`.mmd`, `.mermaid`) files load through their own command-line
tools, so layouts match what those tools draw: `svg.Document.open("graph.dot")` runs `dot -Tsvg`, and
`svg.Document.open("flow.mmd")` runs `mmdc` with SVG (not HTML) labels. The result is an ordinary document to
edit, combine or export to any format. Install Graphviz or `@mermaid-js/mermaid-cli`, or point
`SVGWRITER_DOT` / `SVGWRITER_MMDC` at the executables; a missing tool raises `DiagramToolError` with
the install hint.
Without `mmdc`, Mermaid flowcharts (`graph` / `flowchart`: node shapes, edge styles and labels, chains, `&`
groups, subgraphs) are parsed and laid out by svgwriter itself, so they need no tool at all.

PlantUML (`.puml`) and D2 (`.d2`) load the same way through `plantuml` and `d2`. Math comes from LaTeX
itself: `svg.latex(r"\int_0^1 x^2\,dx = \frac{1}{3}", display=True)` returns the typeset formula as
outlines. Without TeX it falls back to Ziamath (pure Python, `pysvgwriter[math]`) and then to matplotlib's
mathtext; `engine="tex"`, `"ziamath"` or `"mathtext"` picks one.

## Office files

`pip install "pysvgwriter[office]"` adds PowerPoint, Word and Excel:

- `.pptx` out: one slide per drawing (a list gives a deck), each outline an editable PowerPoint shape
  (curves, solid or gradient fill, outline with dashes, caps and joins, transparency, hyperlink), text
  as editable text boxes, images as pictures and SMIL as slide effects. In: shapes, pictures, text
  boxes and effects of a slide (`svg.Document.open("deck.pptx", slide=2)`) as native SVG elements and
  presets, with the same paints and links.
- `.docx` out: the drawing as native Word shapes floating in one paragraph as tall as the drawing,
  with the same outlines, paints, text boxes and pictures as the PowerPoint export. In: paragraphs,
  headings (`Title`, `Heading 1`-`6`), bulleted and numbered lists and line breaks laid out top to
  bottom like Markdown, with each run's bold, italics, underline, strike-through, size, colour and
  font as a styled `<tspan>`. Inline pictures and shapes take their place in the flow; floating ones
  keep their position, and their text boxes come back as text. Table cells are read as paragraphs.
- `.xlsx` out: the drawing as a picture at its natural size.

Formulas made with `svg.latex` remember their source (the group's `data-latex` attribute), so the
PowerPoint and Word exports write them as native, editable Office equations instead of outlines.
The LaTeX goes through MathML (`latex2mathml`) to Office Math: fractions, scripts, roots, sums and
integrals, accents, bars, limits, `\left`/`\right` delimiters, matrices, text and Greek letters.
Each equation is centred on the box the formula occupied, in Cambria Math at the drawn size; in Word
it floats over the shapes, or becomes an equation paragraph when the drawing holds nothing else.
LaTeX with no Office equivalent stays as outlines. Reading a deck back gives an equation's
characters as plain text, without its layout.

```python
import svgwriter as svg

slide = svg.Document(320, 120)
slide.add(svg.latex(r"\int_0^1 x^2\,dx = \frac{1}{3}", display=True)).scale(2).place(160, 60)
slide.save("formula.pptx")      # an editable equation, not shapes
```

Without the extra these formats raise an `ImportError` that names the install command.

## Slide effects

PowerPoint keeps SMIL as slide effects that start with the slide, each at its own `begin` (no clicks
needed), and reading a deck turns them back into `element.animate` presets:

| SMIL (preset) | PowerPoint effect |
| --- | --- |
| opacity 0 to 1, 1 to 0 (`fade_in`, `fade_out`) | Fade entrance, Fade exit |
| `set visibility` (`show`, `hide`) | Appear, Disappear |
| translate or `animateMotion` (`move_by`, `move_to`, `slide_in`, `follow`, `bounce`, `shake`) | custom motion path |
| rotate (`rotate`, `spin`) | Spin |
| scale (`scale`, `grow`, `shrink`, `pulse`) | Grow/Shrink |
| fill or stroke colour (`tween("fill", ...)`, two-colour `color_cycle`) | colour change of the fill or the line |

`begin`, `dur`, `repeat`, `freeze` and there-and-back values (`pulse`, `color_cycle`) carry over; an
ease becomes PowerPoint's accelerate and decelerate fractions, so curves are approximated. Shapes with
an entrance effect are drawn in their visible state, since PowerPoint hides them until the effect.
PowerPoint spins and scales about the shape's centre, so a named or custom pivot (`about=`, `anchor`)
other than the centre is not kept, and motion paths are followed without turning. Anything else
(`morph`, `draw`, `create`, `write`, `wipe`, `typewriter`, `skew`, `blink`, sync-based `begin`) is
dropped with one warning that lists it.
## Pictures where an effect has no shape

TikZ, EPS, PowerPoint, Word, Excalidraw and the polyline formats work from a flattened copy of the
drawing: transforms, clipping, patterns and markers are worked into the shapes themselves. Masks and
filters cannot be. PowerPoint and Word draw an element with a filter or mask as a picture of how it looks
(one warning lists how many); everything else stays editable. `save(..., fallback="drop")` keeps those
elements as shapes without the effect instead, and `dpi=` sets the pictures' resolution (192 by default).
The other flattened formats skip masks and filters with a warning; `el.to_image(scale=...)` turns any
element into a picture by hand.

```python
card = svg.Document(width=200, height=100)
card.rect(10, 10, 80, 50, rx=8, fill="teal", filter=svg.filters.drop_shadow())
# card.save("card.pptx")                   # the shadowed card becomes a picture
# card.save("card.pptx", fallback="drop")  # an editable card without its shadow
```
