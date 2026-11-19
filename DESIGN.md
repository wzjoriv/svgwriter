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

## Other 2.0 decisions

### Model and API
- **Definitions:** IRIs made from an element (`el.ref`, `el.href`, or passing the element as a value) keep a
  pointer to it. When a subtree joins a tree rooted at `<svg>`, or an attribute is set inside one, every
  referenced element without a parent moves into the root `<defs>`; placed targets stay put.
- **Attribute access:** `Element.__getattr__/__setattr__` map Python names to SVG names (`stroke_width`,
  `view_box`, `xlink_href`, `in_`). Known SVG 1.1 names (`attributes.names.KNOWN_ATTRIBUTES`) read `None` when
  unset; unknown names raise `AttributeError` with a "did you mean"; anything else goes through
  `el.set(name, value)`. Typed descriptors (`Attr`) win where they exist. Method names win over attribute
  names; the attribute gets a trailing underscore (`text.rotate_`, `image.color_`).
- **Foreign-namespace attributes** round-trip in Clark notation (`el.set("{uri}name", v)`), written with
  generated `nsN` prefixes declared on the element.
- **Fluent paths:** `Path` has the drawing methods (`move_to`, `line_to`, `curve_to`, `quad_to`,
  `arc_to(rx, ry, x, y, rotation=, large=, clockwise=)`, `close`, ...); `PathBuilder` stays for bare
  `PathData`. Placement is therefore `place(x, y)`, not `move_to`.
- **`PathData` transforms** use `@` only (`M @ data`); `*` is numeric scaling on elements.
- **`path.nodes`** / `PathData.nodes()`: every end and control point as an `(N, 2)` array (absolute; `H`/`V`
  widened to `L`); assigning rewrites `d`, so numpy broadcasting edits nodes. Polylines use `points`.
- **`clone(linked=False)`** deep-copies (pixel arrays too); `linked=True` returns a `<use>` of the original.
  `copy` is an alias (owner's choice), as are `copy.copy`/`copy.deepcopy`.
- **`<use>`**: outline = the target's outline (its own `t`, not its ancestors') offset by `x`/`y`, then the
  use's `t`; `to_path()` styles with the target's presentation attributes over the use's (SVG inheritance).

### Conversions and clipping
- `Convertible` mixin on every graphics element: `to_path()` bakes `t` and the clip into one `<path>`;
  groups, `<a>`, `<switch>`, `<clipPath>` and `<use>` have outlines (union of children), so path ops and
  measurement work on them. Elements without a vector outline (`<image>`) raise `TypeError` naming
  `rasterize()`/`bounds()`. `to_group()` wraps a copy; `rasterize()` renders the element alone over its
  stroke-inclusive bounds; `to_image()` places that raster as an `<image>` where the element was.
- `el.clip(*shapes, units=)` builds a `<clipPath>` (or uses one given) in the element's local coordinates,
  so the clip moves with the element; `unclip()`, `clip_region`, `flatten_clip()`. Outlines intersect with
  the clip region, honouring `clipPathUnits="objectBoundingBox"`.

### Values
- **Colors** (`Color(r, g, b, a=1)`): floats in 0–1 like matplotlib. Tuples/arrays are always 0–1 (a value
  above 1 raises and points to `Color.from_uint8`); strings take names, hex (3/4/6/8 digits), `rgb[a]()`,
  `hsl[a]()`. Output is the name or `#rrggbb`; alpha below 1 on `fill`/`stroke`/`stop-color`/`flood-color`
  becomes the matching `*-opacity` attribute (SVG 1.1 has no alpha in colors); `color`/`lighting-color`
  have no opacity and reject alpha. `np.asarray(color)` is RGBA.
- **numpy:** polyline/polygon `points` are read-only `(N, 2)` float arrays (in an immutable `PointList` value
  so attribute dicts still compare); `Matrix @ (..., 2)` maps arrays in one step; `np.asarray(matrix)` is
  the 3x3 and `Matrix.from_array` reads it back.
- **Images:** `Image(array)` embeds `Pixels`: `color` float32 `(H, W, 1|3)` and `alpha` either the scalar
  `1.0` (opaque, compacted automatically) or `(H, W, 1)`, so `color * alpha` always broadcasts. uint8 input
  is divided by 255; float input must be 0–1. Written lazily as a PNG `data:` URI; a parsed data URI is
  decoded on first pixel access and written back verbatim if untouched. `Image.open(path)`,
  `img.encode(fmt)`, `img.rgba()`.

### Styles and text
- **CSS and computed style** (`attributes.cascade`): style sheets are parsed (comments, groups,
  `!important`; `@` blocks skipped) and matched (type, `*`, `.class`, `#id`, attribute selectors,
  `:first-child`, descendant and child combinators) by specificity. `el.computed(name)` = inline style >
  CSS > presentation attribute > ancestors for inherited properties; `inherit` defers to the parent.
- **Text engine** (`elements/_textlayout.py`): characters are collected across `<text>`/`<tspan>`/`<a>`
  runs with their element chain, whitespace handled per `xml:space` (default: drop newlines, tabs to
  spaces, collapse, trim); each run's font comes from its computed style; `x`/`y`/`dx`/`dy`/`rotate` take
  the innermost element with a value at that character's local index (rotate repeats an element's last
  value); `text-anchor` applies per text chunk. Fonts and glyph outlines are cached (`ops.text.glyph_shape`).
- **Per-character handles:** `text[i]` (`Glyph`) and `text[a:b]` (`GlyphRange`) move (`translate` edits
  `dx`/`dy`: +d at the start, -d after the end) and rotate (`rotate` list) while staying real text; setting
  a presentation attribute on a range (`t[6:11].fill = "red"`) or `wrap(**attrs)` wraps it in a `<tspan>`.
  Scale/skew of part of a text have no SVG form and raise, pointing to `text.glyphs()`, which returns
  index-aligned outline paths styled per run in a `<g>` carrying `t`. `len(text)` and iteration are per
  character; `children` still holds the runs.

### Rendering
- Core: `ops.render_svg(text, w, h)`, `ops.rasterize(doc, scale=, size=, background=)` and
  `el.rasterize()` return float32 straight RGBA arrays in 0–1; `ops.encode(array, "png"|"jpeg"|"webp")`;
  `ops.render_png(doc)`. Document size: `width`/`height`; percentages and missing values fall back to the
  `viewBox` size, then 300.
- skia-python's `SVGDOM` loads no images, draws no text and ignores `<style>`. `ops.render_tree` renders a
  working copy with CSS baked into attributes and each `<text>` replaced by a `<g>` of per-run outline
  paths, and paints embedded images itself in paint order: vector runs between images go through
  `SVGDOM` with other leaves hidden; images are drawn on the same canvas with their transform chain,
  `preserveAspectRatio`, inherited opacity and clip. Known gap: filters/masks on image ancestors.
- skia objects built from Python buffers (`MemoryStream`, `Data`) must own a copy or be kept referenced
  while used; borrowed temporaries caused flaky parses and lossy decodes.

### Conformance
- `python scripts/dev.py svgwriter fetch-suite` downloads the W3C SVG 1.1 SE suite (526 files) into
  `build/conformance/suite`; `... conformance --report build/conformance/report.md` scores it.
- **Round-trip** (original and svgwriter's parse→write, both rendered by skia): 429/430 in scope. The miss
  is skia ignoring XML namespaces (svgwriter's output is the correct one); 4 files skia cannot read are
  excluded.
- **Render** vs the W3C reference PNGs: 146/434, bounded by skia (no SMIL, partial filters) and by the
  suite's SVG fonts, which differ from installed ones.

### Document
- `doc[i]`, `doc[a:b]`, `for el in doc`, `len(doc)` cover top-level *content* (not `<defs>`, `<style>`,
  `<title>`, `<desc>`, `<metadata>`); `doc["id"]` finds any element by id (`KeyError` otherwise);
  `"id" in doc`, `el in doc`. Whole-tree walks are `doc.root.iter()`.
- Anything with `_repr_svg_` (plots, diagrams) can be added (`doc.add(obj)`, `doc += obj`): parsed and wrapped
  in a `<g>` holding its `<svg>`, since a nested `<svg>` cannot take a transform in SVG 1.1.
- **Auto-size:** a document without `width`, `height` and `viewBox` takes its size from the content's
  stroke-inclusive bounds whenever it is written, rendered or displayed (the stored root is not changed);
  `doc.fit(padding)` makes that size permanent. `_repr_svg_`, `_repr_png_`, `doc.rasterize()`,
  `doc.render_png()`.

### Export and import
- `svgwriter.export`: `register(name, extensions=, binary=)` / `register_importer(...)` decorators; lookup by name,
  extension or path (`find_exporter`); `export(doc, fmt)`, `save(doc, path)`, `load(path)`; `doc.save(path)`,
  `doc.export(fmt)`, `Document.open(path)` dispatch through it (`.svg` and text streams keep the SVG writer).
- Built in: SVG, SVGZ, PNG/JPEG/WebP (rasterize + encode), PDF (skia PDF canvas through the same
  `paint_tree` as rasters, so vectors stay vectors), TikZ (`x=1pt, y=-1pt`, so SVG coordinates are kept), EPS,
  DXF R12, HPGL, G-code (mill or laser), Excalidraw. Importers: SVG/SVGZ, raster images, DXF (lines,
  polylines with bulges, circles, arcs, ellipses), HPGL, G-code (cutting moves, arcs, inches, laser),
  Excalidraw (native shapes, arrows, text, images, groups; hand-drawn roughness and hachure drawn clean).
  EPS/PDF/TikZ import would need full interpreters and is left for later.
- Simple vector formats share `export._flatten`: the render copy (CSS resolved, text outlined) reduced to
  painted paths in page coordinates with solid paints; gradients fall back to their first stop, images and
  other unrepresentable content are skipped with a warning. Polyline formats subdivide curves with the
  standard cubic flatness bound and use 96 user units per inch (CSS px).
- Foreign objects: anything with `savefig` (matplotlib figures) or `_repr_svg_` is parsed and added as a
  `<g>` holding its `<svg>`; nested `<svg>` viewports count towards bounds and auto-size.

### Logos and icons (devkit `logo` tool use case)
- A project keeps `logo(**variant) -> Document` in a Python file (`examples/logo.py`); tooling generates every
  asset from it. `rasterize(size=(w, h), padding=p)` fits the padded drawing exactly and centred; raster
  exporters accept `size=int`. ICO (PNG entries, 16..256) and ICNS (PNG entries under standard and Retina
  types) exporters, both importable. All exporters are deterministic (tested), so regenerating and
  comparing bytes detects stale assets.

### Performance (measured with `python scripts/dev.py svgwriter bench`)
- 100k circles: build 13 us, transform 13 us, write 16 us, parse 6 us, bounds 6 us per element. A
  1000x1000 figure rasterizes in ~35 ms and exports PNG in ~50 ms; 200-circle union 0.1 s.
- Fixed hot spots: the unknown-attribute "did you mean" is computed only when shown (`getattr(el, name,
  default)` in the writer cost 400 us/element); n-ary union uses skia's `OpBuilder` once instead of a
  pairwise chain through Python path data (7 s to 0.1 s); raster exporters encode the skia image directly
  instead of round-tripping through float arrays (-30 %); fonts and glyph outlines are cached.
- Tried, not adopted: threads for batch rasterizing (1.1-1.2x on 8 threads: skia-python holds the GIL);
  premultiplied readback with numpy unpremultiply (no gain over skia's conversion for float output).

## Open design questions
- Process pools for very large batches (threads do not help; see Performance).

