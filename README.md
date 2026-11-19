# svgwriter

Build, edit and render vector graphics in Python with a complete SVG 1.1 object model. Shapes move,
rotate and scale through one transform; geometry has boolean operations and measurement; text, images
and colors are first-class (numpy-backed); documents render with skia and export to PNG, PDF, TikZ, DXF
and more. Python 3.10+, `pip install svgwriter` (brings skia-python and numpy).

```python
import svgwriter as svg

doc = svg.Document()                                    # sized to its content when saved or shown
doc.rect(0, 0, 160, 60, rx=12, fill=svg.LinearGradient.horizontal("gold", "tomato"))
doc.circle(30, 30, 18, fill=(1, 1, 1, 0.8))             # colors: names, CSS, or 0-1 tuples (alpha too)
title = doc.text("svgwriter", x=88, y=36, font_size=18, text_anchor="middle")
title[3:].fill = "navy"                                  # style a character range (becomes a <tspan>)

star = svg.builder.star(0, 0, 10, points=5, fill="navy")
doc += star.place(30, 30).rotate(15)                    # placement and rotation go through `t`

doc.save("badge.svg")                                    # also .png .pdf .tex .eps .dxf .ico ...
pixels = doc.rasterize(scale=2)                          # numpy float32 RGBA, shape (rows, cols, 4)
```

## Feature overview

| Area | What you get |
| --- | --- |
| Elements | Every static SVG 1.1 element as a class with a lowercase alias (`svg.Circle` / `svg.circle`); every attribute readable and writable by its Python name (`el.stroke_width`, `el.view_box`) |
| Placement | `el.t` is one affine `Matrix`; `translate`, `rotate`, `scale`, `skew`, `flip_x`/`flip_y` (parent or `local=True` frame) about an `anchor` (bounding-box centre unless pinned); `place(x, y)`, `position`, `bounds()` |
| Operators | `el + (dx, dy)`, `el * 2`, `el @ 30` (rotate), `M @ el`; `a \| b`, `a & b`, `a - b`, `a ^ b` boolean ops on shapes, text, groups and `<use>` |
| Paths | Fluent `svg.path().move_to(0, 0).line_to(10, 0).arc_to(5, 5, 10, 10).close()`; `path.nodes` as an `(N, 2)` array; length, point at length, contains, exact bounds, stroke-to-path, simplify |
| Conversions | `to_path()` (text via glyph outlines, groups merged, clips flattened), `to_image()`, `rasterize()`, `to_group()`, `clone(linked=True)` for `<use>`; clear errors when impossible |
| Clipping | `art.clip(svg.circle(50, 50, 40))` on any element; `flatten_clip()` |
| Text | `text[i]` / `text[a:b]` move, rotate or style characters while staying real text; `tspan` layout, CSS and inherited fonts; `text.glyphs()` for free-form outlines |
| Colors and images | `Color` in 0-1 floats with alpha (auto `*-opacity`); `Image(numpy_array)` with color channels and broadcastable alpha; `Image.open("photo.png")`; Porter-Duff compositing `a \| b` (over), `a & b` (in), `a - b` (out), `a ^ b`, `a * b` (multiply), `a.composite(b, "screen")` |
| Documents | `doc[0]`, `doc["logo"]`, `for el in doc`; auto-size to content; definitions land in `<defs>` when referenced; plots and anything with `_repr_svg_` or `savefig` can be added; notebook display |
| Rendering | skia: `rasterize(size=..., padding=...)` to numpy, embedded and linked images, text, CSS `<style>`; deterministic output |
| Export / import | Registry by name or extension. Out: SVG, SVGZ, PNG, JPEG, WebP, BMP, GIF, PPM, PDF (vector), TikZ, EPS, DXF, HPGL, G-code, Excalidraw, ICO, ICNS. In: SVG, SVGZ, PNG, JPEG, WebP, GIF, BMP, PNM, PDF, TikZ, EPS (their vector paths), DXF, HPGL, G-code, Excalidraw, ICO, ICNS. `svg.export.register(...)` for more |
| Animation | SMIL elements; `doc.render_animation("out.mp4", update=...)` through ffmpeg; `svg.interpolate(a, b, t)` tweens numbers, colors, transforms and morphs any two shapes |

## Geometry in one minute

SVG coordinates are an element's own geometry and are written exactly as given; everything after that
goes through the transform, so the output stays the SVG a person would write.

```python
import svgwriter as svg

c = svg.circle(50, 50, 10)          # writes cx="50" cy="50" r="10"
c.translate(20, 0).rotate(45)       # parent axes by default; local=True for the shape's own axes
print(c.cx, c.position)             # 50.0 (local geometry) and where its centre is now: (70, 50)
print(c.t)                          # shortest equivalent transform text

ring = svg.circle(0, 0, 40) - svg.circle(0, 0, 25)   # boolean difference, a <path>
print(round(ring.total_length(), 1), ring.contains_point(0, 0))
```

`*` and `@` never bake coordinates: `el * 2` is a scaled copy, `el @ 30` a rotated copy and `M @ el` a
copy with matrix `M` applied. Baking is explicit: `el.to_path()` folds the transform into `d`.

## Export and import

```python
doc.save("figure.pdf")                         # vector PDF
doc.save("figure.tex", standalone=True)        # TikZ picture
doc.save("plate.dxf")                          # CAD/CNC polylines in millimetres
doc.save("icon.ico", sizes=(16, 32, 48), padding=4)
svg.Document.open("sketch.excalidraw").save("sketch.svg")
```

## Development

```
pip install -e ".[dev]"
python scripts/dev.py test                     # test tiers
python scripts/dev.py check                    # ruff, tests, docs
python scripts/dev.py svgwriter conformance    # W3C SVG 1.1 suite (after: svgwriter fetch-suite)
python scripts/dev.py svgwriter bench          # timing of the hot paths
```

Design decisions live in [DESIGN.md](DESIGN.md), plans in [ROADMAP.md](ROADMAP.md). MIT licensed.
