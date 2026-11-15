# svgwriter design notes

Living document; the agent finishing the project updates it. Starting state = svgwriter 1.1 (see ROADMAP.md).

## Current architecture (1.1)
- `elements/`: one class per SVG 1.1 element (77 after removing web-only ones). Attributes flow through
  cooperative mixins (`_mixins.py`: core, conditional, style, presentation, xlink, transformable), so a shape's
  `__init__` forwards `**kwargs` through ~9 classes.
- `elements/_factory.py`: `ElementFactory` shortcut methods (`doc.circle(...)`) on Document and containers.
- `elements/_compose.py`, `_geometry.py`: composition operators and skia-backed geometry helpers.
- `path/`: path data model, parser, arcs, builder. `transform/`: matrix and transform lists. `color/`: parsing.
- `io/`: writer, parser, async helpers. `ops/`: skia path ops (currently optional). `video/`: ffmpeg export.
- `cli/`: `python -m svgwriter` (draw, format, info, render, outline, animate).

## Decisions already made by the owner
- skia-python and numpy are required dependencies; there is no optional-skia code path.
- `%` / `%=` for definitions is removed. Referencing an element (`fill=grad`) puts it into `<defs>` when the
  referencing element is added to a document; `doc.define(x)` and `doc.defs += x` do it explicitly.
- Web-only SVG features stay out.
- Images are numpy arrays; alpha stored separately and broadcastable (scalar when uniform).

## Geometry and transform model (2.0)

**Geometry attributes are local; all placement goes through the transform.**
`circle(50, 50, 10)` still writes `cx="50" cy="50" r="10"`: the SVG coordinates are the shape's own
(local) geometry and are written as given, so the output is the SVG a person would write by hand.
Everything after construction (moving, rotating, scaling, skewing) edits the element's transform and never
the geometry. Reading `c.cx` returns the local value; reading where the shape *is* uses `c.position` or
`c.bounds()`.

- **`t`** is the element's transform as one immutable affine `Matrix`. Every move multiplies into it (never
  appends to an op list); the writer emits the shortest equivalent text: rigid motions as
  `rotate(a cx cy)`, otherwise the non-identity parts of `translate rotate skewX scale`, or `matrix(...)` when
  shorter. A parsed `transform` string is kept verbatim until the element is moved. `t` maps to `transform`,
  `gradientTransform` or `patternTransform` depending on the class (`transform_attribute`).
- **`anchor`** is the pivot for rotate/scale/skew, in local coordinates. `None` (default) means the centre
  of the element's local bounding box, recomputed on use, so it follows geometry edits; a tuple pins it.
- **`translate/rotate/scale/skew(..., local=False)`** return `self`. Default is the *parent* frame: the op
  is pre-multiplied (`t = op @ t`), so `translate(10, 0)` moves 10 units right on screen whatever the
  current rotation. `local=True` post-multiplies (`t = t @ op`): axes are the element's own.
  The pivot is the anchor in both frames (mapped through `t` for the parent frame). Angles are degrees.
- **`position`** = the anchor in parent coordinates (read/write; writing translates). `place(x, y)` is
  the chainable form. `bounds()` is the transformed bounding box in parent coordinates.
- **Name clashes:** element methods win over SVG attributes with the same Python name; the attribute gets a
  trailing underscore (`text.rotate_` for `<text rotate="...">`), like `class_`.
- Considered and rejected: rewriting `cx`/`x` on every move (breaks for paths/groups/images, which have no
  single position attribute, and makes rotate/scale impossible to express); storing only an anchor and
  emitting `transform="translate(...)"` for every shape (noisy output, surprising `c.cx`).

### Operators on elements
Element operands keep structural meanings; numbers and pairs transform a copy (in-place forms mutate).

| expression | meaning |
|---|---|
| `a + b` | new `<g>` holding both (moved, not copied); `group += el` appends |
| `el + (dx, dy)`, `el - (dx, dy)` | translated copy; a bare number broadcasts to `(d, d)` like numpy |
| `el * k`, `el / k`, `el * (sx, sy)` | copy scaled about the anchor |
| `el @ degrees` | copy rotated about the anchor ("el at 30°") |
| `M @ el` / `el @ M` | copy with matrix `M` applied in the parent / local frame |
| `a | b`, `a & b`, `a - b`, `a ^ b` | boolean path ops (skia) on shapes, text, groups, `<use>`; result is a `<path>` |
| `+=`, `-=`, `*=`, `/=`, `@=` | the same, in place |

Also `flip_x()` / `flip_y()` (mirror about the anchor). Elements set `__array_ufunc__ = None` (numpy's
opt-out) so `el + np.array([dx, dy])` reaches the element instead of broadcasting into an object array.

`@` follows matrix algebra (`M @ el` reads "apply M to el", like `M @ point`). Baking a transform into
coordinates is explicit: `el.to_path()` returns a `<path>` with `t` folded into `d`.

