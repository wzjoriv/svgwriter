# Geometry and transforms

## Local geometry, one transform

An element's SVG coordinates (`cx`, `x`, `width`, `d`, `points`) are its *local* geometry and are written
exactly as given. Everything that places the element afterwards edits its transform, `t`, an immutable
affine {class}`~svgwriter.Matrix`.

```python
import svgwriter as svg

c = svg.circle(50, 50, 10)
c.translate(20, 0).rotate(90)
print(c.cx)          # 50.0: the local geometry never changes
print(c.position)    # Point(x=70.0, y=50.0): where the anchor (centre) is now
print(c.t)           # the shortest equivalent transform text
print(c)             # <circle cx="50" cy="50" r="10" transform="..."/>
```

## The anchor

Rotation, scaling, skewing and flipping pivot on the **anchor**, given in local coordinates. By default it
is the centre of the element's bounding box and follows geometry edits; set it to pin it.

```python
r = svg.rect(0, 0, 40, 20)
print(r.anchor)              # Point(x=20.0, y=10.0)
r.anchor = (0, 0)            # pivot on the top-left corner from now on
r.rotate(30)
r.anchor = None              # back to the centre
r.rotate(-30, about=(100, 100))     # or pass a pivot for one call
```

## Parent frame or local frame

Each method composes in the **parent** frame by default: `translate(10, 0)` moves ten units right on
screen whatever the current rotation. `local=True` uses the element's own (rotated, scaled) axes.

```python
a = svg.rect(0, 0, 10, 10).rotate(90).translate(10, 0)                 # right on screen
b = svg.rect(0, 0, 10, 10).rotate(90).translate(10, 0, local=True)     # along its own x axis: down
print(a.position, b.position)
```

| method | effect |
| --- | --- |
| `translate(dx, dy)` | move |
| `rotate(degrees, about=None)` | rotate, positive turns from +x towards +y |
| `scale(sx, sy=None, about=None)` | scale; negative factors mirror |
| `skew(x_degrees, y_degrees)` | shear |
| `flip_x()`, `flip_y()` | mirror about the anchor |
| `apply(M)` | compose any matrix |
| `place(x, y)` / `position = (x, y)` | move the anchor to a point |
| `reset()` | drop the transform |

All return the element, so they chain. Gradients and patterns have the same methods; they edit
`gradientTransform` and `patternTransform`.

## Operators

Numbers and pairs transform a **copy**; element operands keep their structural meaning.

```python
dot = svg.circle(0, 0, 5)
moved = dot + (10, 20)          # translated copy
bigger = dot * 2                # scaled copy about the anchor
turned = svg.rect(0, 0, 8, 2) @ 45      # rotated copy ("at 45 degrees")
shifted = svg.Matrix.translate(5, 0) @ dot      # matrix in the parent frame
group = dot + svg.circle(20, 0, 5)              # a <g> holding both
dot += (1, 1)                   # in place
```

`*` and `@` never bake coordinates. To fold the transform into the geometry, convert:
`el.to_path()` returns a `<path>` whose `d` already includes `t`.

Things to keep in mind:

- A bare number broadcasts like numpy: `el + 5` moves by `(5, 5)`, while the method `el.translate(5)`
  follows SVG's `translate(5)` and moves by `(5, 0)`.
- Operators never take elements out of a document: `a + b` copies operands that already have a parent.
  The in-place forms work in place: `a -= b` puts the resulting `<path>` where `a` was, keeping its id.
- `+` groups and `-` cuts, so `a + b - b` is not `a`: the group is cut by `b`'s outline.
- Images composite through their pixels: `img.pixels | other.pixels` (see *Compositing images*); on the
  element, numbers and offsets transform, so `img * 2` scales.

## Bounds

```python
box = svg.rect(0, 0, 10, 10).rotate(45)
print(box.local_bbox())     # before the transform
print(box.bounds())         # after it, in parent coordinates
print(box.exact_bbox())     # tight box of the transformed outline
```

## Placing and aligning

Boxes have edges (`left`, `right`, `top`, `bottom`) and named points (`center`, `top_left`,
`top_center`, `bottom_right`, ...; `box.point("top")` is the middle of the top edge). Elements use the
same names to move by their bounds:

```python
title = svg.rect(0, 0, 80, 20)
badge = svg.circle(0, 0, 6).align(title, "center_left", to="center_right", offset=(4, 0))
note = svg.rect(0, 0, 30, 8).align(title, "top_left", to="bottom_left", offset=(0, 2))
logo = svg.Polygon.regular(0, 0, 10, 5).place(100, 100, at="bottom_right")
print(note.bounds().top, badge.bounds().left)
```

`place(x, y, at=...)` moves a named point onto a coordinate; `align(target, at, to=...)` moves it onto a
point of another element, box or `(x, y)`, so `a.align(b, "top", to="bottom")` stacks `a` under `b`.

## Units and angles

Plain numbers are user units (CSS pixels, 96 per inch). Lengths carry units and combine across them;
the result keeps the left side's unit:

```python
width = 5 * svg.inch - 7 * svg.mm            # 4.7244in
print(width.to("mm"), svg.inch(1) / svg.mm(25.4))
page = svg.Document(210 * svg.mm, 297 * svg.mm)   # A4; coordinates inside are millimetres
# page.save("print.png", dpi=300)
spin = svg.rect(0, 0, 4, 2) @ svg.turn(0.25)  # angles: deg, rad, grad, turn
```

A length times a length is an area and raises; `em`, `ex` and `%` only combine with themselves, because
converting them needs a font size or a reference length. `dpi=` on raster exports sets pixels per inch
(96 is `scale=1`).

## Many elements from arrays

`Class.many(**columns)` builds many elements in one call; scalars apply to all and arrays give one
value each, like numpy broadcasting. Colors can be names, one color, or an `(n, 3|4)` array:

```python
import numpy as np

xs = np.linspace(0, 100, 50)
dots = svg.Circle.many(cx=xs, cy=50 + 20 * np.sin(xs / 10), r=2, fill=np.random.rand(50, 3))
cloud = svg.group(*dots)
```

## Matrices and numpy

```python
import numpy as np

m = svg.Matrix.rotate(90) @ svg.Matrix.scale(2)
points = np.array([[1.0, 0.0], [0.0, 1.0]])
print(m @ points)                    # maps (..., 2) arrays in one step
print(np.asarray(m).shape)           # (3, 3) homogeneous matrix
```
