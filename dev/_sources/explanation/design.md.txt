# Design

The main ideas behind the API:

**Geometry is local; placement is a transform.** SVG coordinates are written as given and never rewritten
by moves. A single immutable affine matrix, `t`, places each element, and the writer turns it into the
shortest equivalent `transform` text. Rewriting `cx` on every move would not work for paths, groups or
images and could not express rotation.

**Operators keep two meanings apart.** Element operands are structural (`a + b` groups, `a - b` subtracts
areas); numbers, pairs and matrices transform a copy (`el + (dx, dy)`, `el * 2`, `el @ 30`, `M @ el`).
Nothing bakes coordinates implicitly.

**Values are numeric and broadcastable.** Colors are 0-1 floats with alpha, images are numpy arrays with
a separate alpha that is a scalar when opaque, point lists and path nodes are `(N, 2)` arrays, and
matrices map arrays in one step.

**Everything converts, or says why not.** Every graphics element can become a path, a group, an image
or pixels; impossible conversions raise a `TypeError` that names the alternative.

**One renderer, extended where skia stops.** skia's SVG renderer draws vectors; svgwriter adds images,
text, CSS and linked files around it on the same canvas, and uses the same painter for PDF.

**Registries over branches.** Exporters and importers, renderers for animation and composite shapes are
registered by name, so third-party code plugs in the same way the built-ins do. Themes are registered
the same way.

**Themes name roles, CSS applies them.** Elements say what they are (`as_role("box")`), a `Theme` says
how each role looks, and the document writes one CSS rule per role in use. The output is ordinary SVG
that any viewer or editor can restyle by changing the sheet, and every svgwriter renderer and exporter
already resolves CSS, so no separate code path exists for themed drawings. A theme is an immutable value:
variants come from `replace`, derived colors are plain functions over typed `Color` methods rather than
an expression language, and the default theme is a context variable set by `with theme:`, not a mutable
module setting, so concurrent code cannot change another's drawings. Theme files hold literals and
`{palette.name}` references only, so loading one never runs code.
