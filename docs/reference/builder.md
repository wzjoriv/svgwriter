# Composite shapes and effects

Presets that build a ready-to-draw element from a few numbers: shapes and lines. Shadows, glows and
markers are in the [preset libraries](presets.md). Every preset forwards keyword arguments to the element it builds, so `fill=`, `stroke=` and
`id=` work as they do on the plain classes, and the result takes transforms, `place(...)` and boolean
operations like any other element.

| Preset | Signature | Returns |
| --- | --- | --- |
| `star` | `star(cx, cy, outer, inner=None, points=5, *, corner_radius=0)` | `Polygon`, or `Path` when rounded |
| `regular_polygon` | `regular_polygon(cx, cy, r, sides, *, rotation=0, corner_radius=0)` | `Polygon`, or `Path` when rounded |
| `gear` | `gear(cx, cy, radius, teeth=12)` | `Polygon` |
| `heart` | `heart(cx, cy, size)` | `Path` |
| `cross` | `cross(cx, cy, size, *, thickness=None)` | `Polygon` |
| `callout` | `callout(x, y, width, height, *, tail, corner_radius=8)` | `Path` |
| `arrow` | `arrow(x1, y1, x2, y2, head=10)` | `Path` |
| `grid` | `grid(x, y, width, height, *, rows, cols)` or `*, spacing` | `Path` |
| `spiral` | `spiral(cx, cy, *, turns, start_radius, end_radius)` | `Path` |
| `wave` | `wave(x, y, width, *, amplitude, wavelength, kind="sine")` | `Path` |

```python
import svgwriter as svg
from svgwriter import builder

doc = svg.Document(240, 120)
doc += builder.callout(10, 10, 120, 50, tail=(40, 100), fill="white", stroke="black")
doc += builder.heart(180, 40, 50, fill="crimson")
doc += builder.wave(10, 100, 220, amplitude=6, wavelength=40, stroke="steelblue")
badge = builder.regular_polygon(180, 85, 14, 6, corner_radius=3, fill="gold")
cutout = badge - builder.cross(180, 85, 14)
```

Presets carry a [theme role](../guides/themes.md), so they follow the document theme: registered shapes
are `shape` (filled with the palette's primary color), `callout` is `box`, `arrow` is `arrow.line`, `grid`
is `grid`, `spiral` and `wave` are `line`; `outline`, `dashed_line` and `dot`
are `outline`, `line` and `dot`. Presentation keywords you pass go into the inline
`style`, so they win over the role. `grid`, `spiral` and `wave` return open paths with `fill="none"`.
`wave` takes `kind="sine"` (smooth cubic segments), `"square"`, `"triangle"` or `"sawtooth"`.

## Your own presets

A shape preset is a function that returns an element. Decorating it with `@svg.preset.shape`
registers it under the function's name (or `name=`) beside the built-in shapes (the list behind `svgwriter shapes`), and checks at call time
that it really returns an element. A taken name raises `ValueError` naming the function that owns it,
built-in shapes included; `replace=True` replaces one on purpose. `svg.preset.shape(role="shape")`
gives the built elements a theme role; `role=None` leaves them unthemed.

```python
import svgwriter as svg


@svg.preset.shape
def badge(cx: float, cy: float, r: float, **kwargs: object) -> svg.Group:
    ring = svg.Circle(cx, cy, r, fill="none", stroke="black")
    dot = svg.Circle(cx, cy, r / 3, **kwargs)
    return svg.Group(ring, dot)


print("badge" in svg.preset.list("shape"), badge(10, 10, 6, fill="gold").tag)
make = svg.preset.get("shape", "badge")
svg.preset.unregister("shape", "badge")
```

Follow the conventions of the built-in presets so yours feel the same: position and size as
positional arguments, options as keyword-only arguments, and style attributes passed through
`**kwargs` to the element. A package can publish presets by defining them with `svg.preset.shape` in a
module; importing that module registers them. `svg.preset.get("shape", name)` then looks a preset up by
name, and `svg.preset.list("shape")` lists everything available. Animation presets work the same way
(see the [animation guide](../guides/animation.md)), and so do patterns, filters, gradients, markers and
text effects (see the [Presets guide](../guides/presets.md)).

## Preset functions

```{eval-rst}
.. automodule:: svgwriter.preset
   :members:
```

```{eval-rst}
.. automodule:: svgwriter.builder
   :members:
```
