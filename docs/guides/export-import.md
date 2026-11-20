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
| PDF | `.pdf` | yes | yes | vector, via skia; `title`, `author`; reads paths, images, clips and text, `page=` |
| TikZ | `.tikz .tex` | yes | yes | `standalone=True` for a compilable document; SVG coordinates kept (`x=1pt, y=-1pt`) |
| EPS | `.eps .ps` | yes | yes | PostScript has no transparency |
| DXF | `.dxf` | yes | yes | R12 polylines in mm, layer per colour; reads lines, polylines with bulges, circles, arcs, ellipses |
| HPGL | `.hpgl .plt` | yes | yes | pen plotters and cutters, one pen per colour |
| G-code | `.gcode .nc .ngc` | yes | yes | `mode="mill"` or `"laser"`, `feed`, `cut_z`, `tolerance` |
| Excalidraw | `.excalidraw` | yes | yes | imports native shapes, arrows, text, images and groups |
| ICO, ICNS | `.ico .icns` | yes | yes | PNG entries at `sizes=`, `padding=` |

TikZ, EPS and the polyline formats work from a flattened copy of the drawing: gradients become their
first colour and images are skipped with a warning.

PDF, EPS and TikZ read back as filled and stroked `<path>` elements with solid colours, stroke width,
dashes, caps, joins and opacity, in points with y pointing down. The PDF reader scans for objects (a
broken xref table does not matter), inflates `/FlateDecode` streams, follows Form XObjects and `gs`
alpha, and reads page 1 unless you pass `page=`; images, clipping paths and text come in as `<image>`,
`clip-path` and `<text>` (single-byte fonts), while shadings and tiling patterns are skipped. The
EPS reader is a small PostScript interpreter: paths, `arc`, painting, colours, line styles,
`gsave`/`grestore`, transforms, and procedures and dictionaries with `def`, honouring
`%%BoundingBox`; it ignores operators it does not know. The TikZ reader takes `\draw`, `\fill`,
`\filldraw` and `\path` with `--`, `.. controls ..`, `cycle`, `rectangle` and `circle`, colours from
`\definecolor` and xcolor mixes, and the common line options; macros, `\foreach`, styles and nodes
are not expanded.

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

PlantUML (`.puml`) and D2 (`.d2`) load the same way through `plantuml` and `d2`. Math comes from LaTeX
itself: `svg.latex(r"\int_0^1 x^2\,dx = \frac{1}{3}", display=True)` returns the typeset formula as
outlines (needs `latex` and `dvisvgm`, both in TeX Live and MiKTeX).

## Office files

`pip install "svgwriter[office]"` adds PowerPoint, Word and Excel:

- `.pptx` out: one slide sized like the drawing, each outline an editable PowerPoint shape (curves,
  fill, outline, transparency) and images as pictures. In: shapes, pictures and text boxes of a slide
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

