# svgwriter roadmap

Decisions and their reasons are in [DESIGN.md](DESIGN.md); this file lists what 2.0 delivered and what is
left for later.

## Done in 2.0

1. **Required skia-python and numpy.** No optional code paths; geometry, text and rendering always work.
2. **One transform model.** Geometry attributes stay as written; `t` is an affine `Matrix` written as the
   shortest equivalent `transform`. `translate`, `rotate`, `scale`, `skew`, `flip_x`/`flip_y` in the parent
   or local frame about an `anchor`; `place`, `position`, `bounds()`. Gradients, patterns and clip paths
   share it (`gradientTransform`, `patternTransform`).
3. **Operators.** `el + (dx, dy)`, `el * k`, `el / k`, `el @ degrees`, `M @ el`, `el @ M`, in-place forms;
   `|`, `&`, `-`, `^` boolean operations on shapes, text, groups and `<use>`.
4. **Definitions without `%`.** Referenced elements move into `<defs>` when they join a document.
5. **Fluent paths** (`path().move_to(...).line_to(...).close()`) and `path.nodes` as a numpy array.
6. **Conversions everywhere** with clear errors: `to_path`, `to_image`, `rasterize`, `to_group`,
   `clone(linked=)`; clipping with `clip()` / `flatten_clip()`.
7. **Path operations** through skia: union (n-ary with `OpBuilder`), intersection, difference, xor,
   simplify, stroke-to-path, exact bounds, contains, length, point and tangent at length.
8. **Attribute access** for every SVG property by Python name, with "did you mean" for typos in reads,
   writes and constructor keywords; length reads are floats unless a unit is present.
9. **Values.** Colors as 0-1 floats with alpha (CSS in, SVG out, automatic `*-opacity`); numpy images with
   separate color and broadcastable alpha; numpy point and node arrays; `Matrix @ (N, 2)` arrays.
10. **Text.** Layout across `tspan`s with computed fonts and SVG positioning lists; `text[i]` and
    `text[a:b]` handles that move, rotate and style characters while staying text; `glyphs()` outlines.
11. **CSS.** Style sheets parsed and matched; `el.computed(name)` with inheritance.
12. **Documents.** Indexing by position and id, content iteration, auto-size, `fit()`, ingestion of
    `_repr_svg_` objects and matplotlib figures, notebook SVG and PNG display.
13. **Rendering** with skia including what skia's SVG renderer lacks: embedded and linked images, text,
    CSS; exact sizes with padding; deterministic output.
14. **Export/import registry** by name or extension: SVG, SVGZ, PNG, JPEG, WebP, PDF, TikZ, EPS, DXF, HPGL,
    G-code, Excalidraw, ICO, ICNS out; SVG, SVGZ, raster images, PDF, TikZ, EPS, DXF, HPGL, G-code,
    Excalidraw, ICO, ICNS in (PDF, TikZ and EPS as their vector paths).
15. **Performance**, measured (`dev.py svgwriter bench`): 100k elements build, write and parse in about
    1.3, 1.6 and 0.6 s; raw RGBA animation frames; threads measured and not adopted.
16. **Conformance tooling** for the W3C SVG 1.1 suite: round-trip 429/430, render 148/434.
17. **Housekeeping.** Web-only features out, SMIL and ffmpeg video kept, modern typing, geometry-first
    attribute order, `pathdata` sub-package (no clash with `svg.path`), `builder` reduced to composite
    shapes and effects, devkit tooling, tests mirroring the package.
18. **Image compositing.** Porter-Duff `img | b`, `& b`, `- b`, `^ b` and `* b` (multiply), plus
    `composite(b, operator)` with every `feComposite` operator and `feBlend` mode; any element can be
    the other operand; `ops.composite_rgba` on raw arrays.
19. **More formats.** BMP, GIF, PPM out and PNM in (pure numpy); PDF, EPS/PS and TikZ in (vector subset);
    Graphviz DOT and Mermaid in through their tools; `svgwriter[office]`: PowerPoint shapes both ways,
    Word and Excel pictures out. A round-trip test renders every readable format against the original.
20. **Usability pass** from an independent review: operators never take elements out of a document and
    in-place forms replace in the parent; `text_content`; colors checked on assignment; path drawing
    needs `move_to`; clearer errors; `Character` handles by grapheme cluster; vector `Point`; typed
    `doc.rect(...)` shortcuts; one way to do each job; readable `rotate` text about the element's anchor.
21. **Layout and motion.** Named box points and `place(..., at=)` / `align(...)`; `svg.interpolate` for
    numbers, colors, matrices, paths and elements (shape morphing); `doc[i] = el`.
22. **Filters as graphs** (`Filter(last)` collects inputs, `a >> b`, `f1 >> f2`), pattern conversions
    (`to_image`, `from_image`, `expand_pattern`) and `register_font` for font files.

## Later

- **SMIL evaluation.** Apply `<animate>` values at time *t* so animations render without an `update`
  callback (also lifts the conformance render score in the animate chapter).
- **Filters and masks on images** in the renderer (images are drawn outside skia's SVG pass today).
- **Gradients and patterns in TikZ and EPS** as native shadings instead of the first-stop fallback;
  images in EPS (`colorimage`).
- **Fuller EPS, PDF and TikZ import**: text, images, shadings and clipping; PostScript control flow;
  TikZ macros, styles and `\foreach`.
- **`textPath` layout** and SVG fonts (`<font>`, `<glyph>`) in the text engine.
- **Id index** kept by `Element.id` so `doc["id"]` is constant time on very large documents.
- **Process pools** for very large rasterizing batches (threads do not help: skia holds the GIL).
- **Complex text shaping** (ligatures, Arabic, Indic) once a HarfBuzz-backed shaper is reachable from
  Python without a heavy dependency.
- **Video in**: frames of a video as lazy `Image`s (`video[i]`) through ffmpeg, to mix footage with
  vector animation in `update`.
- **Batch elements**: numpy-vectorized creation and transforms for very many similar shapes.
- **matplotlib round trip**: elements back into matplotlib artists, beyond today's figure import.
- **Split** `elements/base.py` (tree, query, ids) and `document.py` (sizing, ingest) into private modules.
- **Logo assets.** A devkit `logo` tool will import a project's `logo(**variant)` and write SVG variants,
  PNGs, `.ico`, `.icns`, favicons and webmanifest icons; svgwriter's side is done (`examples/logo.py`).
