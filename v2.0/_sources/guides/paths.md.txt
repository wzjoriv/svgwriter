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

## Measurement

```python
ring = svg.circle(50, 50, 40) - svg.circle(50, 50, 20)
print(ring.total_length())
print(ring.point_at_length(10))
print(ring.contains_point(50, 50), ring.contains_point(15, 50))
print(ring.exact_bbox())
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
