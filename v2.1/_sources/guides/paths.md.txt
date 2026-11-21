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
a, b = svg.path("M0 0 H10 V10 H0 Z"), svg.path("M5 0 H15 V10 H5 Z")
joined = a + b                                # two subpaths, overlap filled (nonzero)
holed = (a + b).update(fill_rule="evenodd")   # overlap left empty
merged = a | b                                # one outline, overlap filled under any rule
print(joined.contains_point(7, 5), holed.contains_point(7, 5), merged.contains_point(7, 5))
```

## Measurement

```python
ring = svg.circle(50, 50, 40) - svg.circle(50, 50, 20)
print(ring.total_length())
print(ring.point_at_length(10))
print(ring.contains_point(50, 50), ring.contains_point(15, 50))
print(ring.exact_bbox())
```

## Walking along a path

Every outline can be walked by fraction of its length, 0 at the start and 1 at the end:

```python
wave = svg.path("M0 50 C40 0 60 100 100 50", stroke="black", fill="none")
print(wave.at(0.5), wave.tangent_at(0.5), wave.normal_at(0.5))
points = wave.sample(5)                       # evenly spaced by distance
middle = wave.between(0.25, 0.75)             # a new <path> with the same style
first = wave.between(0, 20, by="length")      # or by distance
ticks = svg.distribute([svg.rect(-1, -4, 2, 8) for _ in range(9)], along=wave)   # turned to follow it
```

`normal_at` is the tangent turned a quarter counter-clockwise on screen, which points outwards on
rectangles, circles and ellipses. `sample` and `distribute` on a closed outline do not repeat the start.

## Corners

`corners()` lists the sharp vertices: their number (segment end points counted in drawing order),
position and the angle the outline turns there. `round_corners` replaces them with circular arcs (or
quadratics with `fillet="quad"`) on any shape; fillets shrink when the sides are too short:

```python
tri = svg.polygon([(0, 0), (60, 0), (0, 40)], fill="gold")
print([(c.index, round(c.angle.degrees)) for c in tri.corners()])
soft = tri.round_corners(6)                                   # every corner
blunt = tri.round_corners(6, where=lambda c: c.angle > 120)   # only the sharpest
one = tri.round_corner(1, 4, fillet="quad")                   # a single vertex
```

## Clipping

```python
art = svg.rect(0, 0, 100, 100, fill="teal").clip(svg.circle(50, 50, 40))
print(art.clip_region)                  # the <clipPath>, defined automatically
flat = art.flatten_clip()               # one path with the clip applied
art.unclip()
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
