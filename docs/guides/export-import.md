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
| PDF | `.pdf` | yes | | vector, via skia; `title`, `author` |
| TikZ | `.tikz .tex` | yes | | `standalone=True` for a compilable document; SVG coordinates kept (`x=1pt, y=-1pt`) |
| EPS | `.eps .ps` | yes | | PostScript has no transparency |
| DXF | `.dxf` | yes | yes | R12 polylines in mm, layer per colour; reads lines, polylines with bulges, circles, arcs, ellipses |
| HPGL | `.hpgl .plt` | yes | yes | pen plotters and cutters, one pen per colour |
| G-code | `.gcode .nc .ngc` | yes | yes | `mode="mill"` or `"laser"`, `feed`, `cut_z`, `tolerance` |
| Excalidraw | `.excalidraw` | yes | yes | imports native shapes, arrows, text, images and groups |
| ICO, ICNS | `.ico .icns` | yes | yes | PNG entries at `sizes=`, `padding=` |

TikZ, EPS and the polyline formats work from a flattened copy of the drawing: gradients become their
first colour and images are skipped with a warning.

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
