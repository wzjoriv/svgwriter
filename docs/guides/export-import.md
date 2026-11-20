# Export and import

Formats are found by name or file extension, so `save` and `open` usually need nothing else:

```python
import svgwriter as svg

doc = svg.Document(120, 80)
doc.rect(10, 10, 100, 60, rx=8, fill="gold", stroke="black")
doc.text("svgwriter", x=60, y=48, font_size=16, text_anchor="middle")

doc.save("figure.svg")
doc.save("figure.png", scale=2)
doc.save("figure.pdf")
doc.save("figure.tex", standalone=True)
data = doc.export("eps")                      # bytes or str, without a file
again = svg.Document.open("figure.svg")
print(sorted(svg.export.exporters()))
```

| format | extensions | out | in | notes |
| --- | --- | --- | --- | --- |
| SVG | `.svg` | yes | yes | links, `<a>` and ids preserved; `pretty`, `precision` options |
| SVGZ | `.svgz` | yes | yes | gzip-compressed SVG |
| PNG, JPEG, WebP | `.png .jpg .jpeg .webp` | yes | yes | `scale`, `size`, `padding`, `background`, `quality`; imports become an `<image>` |
| PDF | `.pdf` | yes | yes | vector, via skia; selectable text; `title`, `author`, `text`; reads paths, images, clips, text and shadings, `page=` |
| TikZ | `.tikz .tex` | yes | yes | `standalone=True` for a compilable document; text as `\node`; SVG coordinates kept (`x=1pt, y=-1pt`) |
| EPS | `.eps .ps` | yes | yes | text in the standard fonts; PostScript has no transparency |
| DXF | `.dxf` | yes | yes | R12 polylines in mm, layer per colour; reads lines, polylines with bulges, circles, arcs, ellipses |
| HPGL | `.hpgl .plt` | yes | yes | pen plotters and cutters, one pen per colour |
| G-code | `.gcode .nc .ngc` | yes | yes | `mode="mill"` or `"laser"`, `feed`, `cut_z`, `tolerance` |
| Excalidraw | `.excalidraw` | yes | yes | imports native shapes, arrows, text, images and groups |
| ICO, ICNS | `.ico .icns` | yes | yes | PNG entries at `sizes=`, `padding=` |

TikZ, EPS and the polyline formats work from a flattened copy of the drawing. TikZ writes gradients
as shadings and EPS as `shfill`; the polyline formats take their first colour. EPS embeds images,
the others skip them with a warning.

### Text stays text

Every format that can hold text keeps it as text, so it can be selected, searched and edited. Where
a format cannot hold some text exactly, that text is drawn as its glyph outlines, which look the
same but are shapes. Only raster formats turn text into pixels.

| format | kept as text | drawn as outlines |
| --- | --- | --- |
| SVG, SVGZ, HTML | everything | nothing |
| PDF | plain-coloured text in scripts that need no shaper (Latin, Greek, Cyrillic, CJK, ...), in an embedded font subset | gradient or pattern paint, filters, masks, shaped scripts (Devanagari, Arabic, ...) |
| TikZ | everything, as `\node` with size, family, weight, style, colour, opacity and rotation | nothing |
| EPS | ASCII text in Helvetica, Times or Courier | other characters |
| PowerPoint | everything, as text boxes with font, size, weight, style, colour, opacity and rotation | nothing |

Pass `text=False` to `pdf`, `tikz` or `eps` to get exact outlines everywhere, for example when the
reader of the file may lack the fonts:

```python
doc.save("figure.pdf")                 # selectable text
doc.save("figure.pdf", text=False)     # glyph outlines only
```

PDF, EPS and TikZ read back as filled and stroked `<path>` elements with solid colours, stroke width,
dashes, caps, joins and opacity, in points with y pointing down. The PDF reader scans for objects (a
broken xref table does not matter), inflates `/FlateDecode` streams, follows Form XObjects and `gs`
alpha, and reads page 1 unless you pass `page=`. Images, clipping paths and text come in as
`<image>`, `clip-path` and `<text>`. Text is decoded through the font's `/ToUnicode` map, which most
PDF writers embed. Glyphs placed one at a time are joined back into words, and the font family
comes from the font's name. Axial and radial shadings become gradients and tiling patterns become
`<pattern>`. The EPS reader is a small PostScript interpreter. It handles paths, `arc`, painting,
colours, line styles, `gsave`/`grestore`, transforms, `image`/`colorimage`, `clip`, `show` with
`findfont`, and procedures and dictionaries with `def`. It honours `%%BoundingBox` and ignores
operators it does not know. The TikZ reader takes `\draw`, `\fill`, `\filldraw` and `\path` with
`--`, `.. controls ..`, `cycle`, `rectangle` and `circle`. It also reads colours from `\definecolor`
and xcolor mixes, the common line options, nodes (with shapes and names), `\tikzset` styles,
`scope` and `\foreach`. Other macros are not expanded.

```python
page = svg.export.load("figure.pdf", page=0)
picture = svg.Document.open("figure.tex")
```

## Your own formats

```python
@svg.export.register("count", extensions=(".count",), binary=False)
def count(document, **options):
    """Number of top-level elements."""
    return str(len(document))

doc.save("figure.count")

@svg.export.register_importer("lines", extensions=(".lines",))
def read_lines(data, **options):
    """One polyline per text line of x,y pairs."""
    out = svg.Document()
    for line in data.decode().splitlines():
        pairs = [tuple(map(float, p.split(","))) for p in line.split()]
        out.add(svg.polyline(pairs, fill="none", stroke="black"))
    return out

svg.export.unregister("count")                       # plugins and tests can clean up
svg.export.unregister("lines", importer=True)
```

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

- `.pptx` out: one slide sized like the drawing, each outline an editable PowerPoint shape (curves,
  fill, outline, transparency), text as editable text boxes and images as pictures. In: shapes, pictures and text boxes of a slide
  (`svg.Document.open("deck.pptx", slide=2)`) as native SVG elements.
- `.docx` and `.xlsx` out: the drawing as a picture at its natural size.

Without the extra these formats raise an `ImportError` that names the install command.

## HTML pages

`doc.save("page.html")` writes a standalone page with the drawing inline. The SVG stays static;
interaction is attached by the page, by element id:

```python
# doc.save("page.html", title="Demo", css="#logo:hover { opacity: 0.7 }",
#          handlers={"logo": {"click": "this.style.fill = 'red'"}})
```

Opening an HTML file reads its first inline `<svg>`.

