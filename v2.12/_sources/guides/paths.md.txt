# Paths, boolean operations and measurement

## Building paths

```python
import svgwriter as svg

p = (svg.path(stroke="black", fill="none")
     .move_to(10, 90)
     .line_to(50, 10)
     .curve_to(60, 0, 80, 0, 90, 10)
     .arc_to(20, 20, 90, 50, clockwise=True)
     .close())
print(p.d)
```

Drawing methods: `move_to`, `line_to`, `horizontal_to`, `vertical_to`, `curve_to`, `smooth_curve_to`,
`quad_to`, `smooth_quad_to`, `arc_to(rx, ry, x, y, rotation=0, large=False, clockwise=True)`, `close`.
Each takes `relative=True` for the lowercase command. Path data text works too: `svg.path("M0 0 H10")`.

## Nodes as arrays

`path.nodes` is every end point and control point as an `(N, 2)` array. Assigning it rewrites `d`, so
numpy broadcasting edits the whole path at once:

```python
import numpy as np

wave = svg.path().move_to(0, 0)
for x in range(10, 101, 10):
    wave.line_to(x, 0)
wave.nodes = wave.nodes + np.column_stack([np.zeros(11), 5 * np.sin(np.arange(11))])
poly = svg.polyline(np.column_stack([np.linspace(0, 100, 50), np.random.rand(50) * 10]))
print(poly.points.shape)        # (50, 2), read-only
```

## Boolean operations

Shapes, text, groups and `<use>` all have outlines, so they combine:

```python
a, b = svg.circle(0, 0, 30), svg.rect(0, -10, 60, 20)
union = a | b
inter = a & b
cut = a - b
either = a ^ b
logo = svg.rect(0, 0, 120, 50) - svg.text("SVG", x=10, y=40, font_size=40)
many = a.union(b, svg.circle(40, 0, 10))      # n-ary, one skia operation

row = svg.Document(780, 110)                  # the results side by side, each in its own colour
row += [a.update(fill="#ccc", opacity=0.7).translate(50, 45), b.update(fill="#999", opacity=0.7).translate(50, 45)]
labels = [(union, "a | b", "steelblue"), (inter, "a & b", "tomato"), (cut, "a - b", "seagreen"),
          (either, "a ^ b", "gold"), (logo, "rect - text", "purple"), (many, "a.union(b, c)", "teal")]
for x, (shape, label, color) in zip([150, 250, 350, 450, 580, 700], labels):
    row.add(shape.update(fill=color).place(x, 45))
    row.text(label, x=x, y=104, font_size=11, text_anchor="middle")
```

Results are `<path>` elements carrying the left operand's style. `simplified()` removes overlaps, and
`stroked()` turns a stroke into a filled outline.

Boolean operations combine filled areas. An open path (no `Z`) is treated as closed by a straight line,
so a lone line encloses nothing; when that leaves the result empty, svgwriter warns. Turn a line into
an area with `stroked()` first.

`+` is not a union: it joins the outlines as subpaths of one `<path>`, and the `fill-rule` then decides
what the overlap looks like. With `nonzero` (the default) overlapping outlines drawn the same way round
fill the overlap; with `evenodd` the overlap becomes a hole. `|` computes the true union, so the result
is the same under either rule:

```python
a, b = svg.path("M0 0 H40 V40 H0 Z", fill="steelblue"), svg.path("M20 0 H60 V40 H20 Z", fill="tomato")
joined = a + b                                # two subpaths, overlap filled (nonzero)
holed = (a + b).update(fill_rule="evenodd")   # overlap left empty
merged = a | b                                # one outline, overlap filled under any rule
print(joined.contains_point(28, 20), holed.contains_point(28, 20), merged.contains_point(28, 20))

row = svg.Document(350, 50, view_box=(-5, 0, 350, 50))                   # the operands, then the three results
row += [a.update(opacity=0.6), b.update(opacity=0.6)]
row += [shape.update(fill="seagreen").translate(90 * n + 100, 0) for n, shape in enumerate([joined, holed, merged])]

```

## Measurement

```python
ring = svg.circle(50, 50, 40) - svg.circle(50, 50, 20)
print(ring.total_length())
print(ring.point_at_length(10))
print(ring.contains_point(50, 50), ring.contains_point(15, 50))
print(ring.exact_bbox())
marked = svg.Document(100, 100)               # the ring with the point 10 units along it marked
marked += [ring.update(fill="steelblue"), svg.circle(*ring.point_at_length(10), 3, fill="tomato")]
```

## Walking along a path

Every outline can be walked by fraction of its length, 0 at the start and 1 at the end:

```python
wave = svg.path("M0 50 C40 0 60 100 100 50", stroke="steelblue", stroke_width=4, fill="none")
print(wave.at(0.5), wave.tangent_at(0.5), wave.normal_at(0.5))
points = wave.sample(5)                       # evenly spaced by distance
middle = wave.between(0.25, 0.75)             # a new <path> with the same style
first = wave.between(0, 20, by="length")      # or by distance
ticks = svg.distribute([svg.rect(-1, -4, 2, 8) for _ in range(9)], along=wave)   # turned to follow it

board = svg.Document(100, 100)
board += [wave, middle.update(stroke="crimson", stroke_width=6), *ticks, first.update(stroke="orange", stroke_width=6)]
board += [svg.circle(*point, 3, fill="gold", stroke="black") for point in points]
```

`normal_at` is the tangent turned a quarter counter-clockwise on screen, which points outwards on
rectangles, circles and ellipses. `sample` and `distribute` on a closed outline do not repeat the start.

## Corners

`corners()` lists the sharp vertices: their number (segment end points counted in drawing order),
position and the angle the outline turns there. `round_corners` replaces them with circular arcs (or
quadratics with `fillet="quad"`) on any shape; fillets shrink when the sides are too short:

```python
tri = svg.polygon([(0, 0), (60, 0), (0, 40)], fill="gold", stroke="black")
print([(c.index, round(c.angle.degrees)) for c in tri.corners()])
soft = tri.round_corners(6)                                   # every corner
blunt = tri.round_corners(6, where=lambda c: c.angle > 120)   # only the sharpest
one = tri.round_corner(1, 4, fillet="quad")                   # a single vertex

row = svg.Document(340, 70)                                   # the four side by side
for n, (shape, label) in enumerate([(tri, "tri"), (soft, "soft"), (blunt, "blunt"), (one, "one")]):
    row.add(shape.update(stroke="black").translate(90 * n + 10, 10))
    row.text(label, x=90 * n + 40, y=64, font_size=12, text_anchor="middle")
```

## Path effects

These turn an outline into new geometry, so every format (PDF, PowerPoint, DXF, plotters) draws the result
as it looks here:

- `roughen(segment, deviation, seed=)` breaks the outline into short pieces that wobble, for a hand-drawn look;
  the same seed draws the same wobble.
- `dashed(*intervals, offset=)` cuts it into dashes as open paths, for formats that have no dash support.
- `stamp(shape, spacing, orient=)` repeats a shape along it (`"rotate"` with the path, `"translate"` upright,
  `"morph"` bent along it), for dotted lines, arrows along a curve or ticks.

```python
doc = svg.Document(width=420, height=150)
doc.add(svg.rect(20, 20, 110, 70, rx=10, fill="#fde68a", stroke="#92400e", stroke_width=2).roughen(seed=2))
doc.add(svg.circle(210, 60, 40, fill="none", stroke="#0ea5e9", stroke_width=3).dashed(12, 6))
doc.add(svg.path("M290 90 C320 20 350 140 400 60", fill="#e11d48")
        .stamp(svg.Polygon([(-4, -4), (5, 0), (-4, 4)]), 14))      # an arrowhead every 14 units
doc.add(svg.path("M20 125 L400 125", fill="#334155").stamp(svg.rect(-1, -6, 2, 12), 10))
```

Every path effect is also a registered preset: `el.path_effect("taper", widths=(0, 8, 0))` applies one by
name, and `taper(*widths)` draws a brush stroke whose width changes along the line (one width per point
spread evenly, or `widths=` a function of the position 0..1), filled with the element's stroke paint. Add
your own with `@svg.preset.path_effect`: a function from path data to path data (`fills=True` when the
result is an outline to fill). Plugins ship them through the `svgwriter.path_effect` entry point.

```python
brush = svg.path("M20 80 C80 10 140 110 200 40", stroke="#1e3a8a").taper(0, 14, 0)


@svg.preset.path_effect(fills=True)
def thicken(data: svg.PathData, *, width: float = 4) -> svg.PathData:
    return svg.path(data).stroked(width=width).get("d")


bar = svg.line(20, 100, 200, 100, stroke="#0f766e", fill="#0f766e").path_effect("thicken", width=12)
svg.preset.path_effect.unregister("thicken")
```

## Clipping

```python
doc = svg.Document(100, 100)
doc.rect(0, 0, 100, 100, fill="none", stroke="#999", stroke_dasharray="4 2")      # the unclipped square
art = doc.rect(0, 0, 100, 100, fill="teal").clip(svg.circle(50, 50, 40))
print(art.clip_region)                  # the <clipPath>, defined automatically
flat = art.flatten_clip()               # one path with the clip applied
art.clone().unclip()                    # the square again, on a copy
```

The clip shapes are in the element's local coordinates, so the clip moves with the element.

## Conversions

| method | result |
| --- | --- |
| `to_path()` | a `<path>` with the transform and clip baked in (text through glyph outlines) |
| `to_group()` | a `<g>` holding a copy |
| `to_image(scale=)` | an `<image>` with the rasterized element, placed where it was |
| `rasterize(scale=)` | a numpy RGBA array |
| `clone()` / `clone(linked=True)` | a deep copy, or a `<use>` that renders the original |

Conversions that cannot work raise a `TypeError` that says why and what to use instead, for example
`svg.Image("photo.png").to_path()`.
