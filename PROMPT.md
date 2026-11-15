# PROMPT: finish svgwriter

You are taking over `svgwriter`, a Python library for building, editing and rendering vector graphics with an
SVG 1.1 object model. It started as a stress-test demo for the `stubpy` stub generator and is now its own
project. The code here is version 1.1 from that demo: read `README.md`, `ROADMAP.md`, `DESIGN.md` and the
package before changing anything. Treat it as a real product: great user experience first, then breadth.

Owner: Josue N Rivera. Work on branches, never commit or push without the owner's go-ahead (stage and stop).

## How to work
- Read `DESIGN.md` first; keep it current as you decide things. Keep a git-ignored `TODO.md` of OPEN work only, headed
  "(open work only: delete an item when it is done; history is in git; ideas for later in LATER.md)": prune
  each item the moment it is done, never keep a done log; put unscheduled ideas in a git-ignored `LATER.md`.
- Temp files only in your session scratchpad (full Windows path), never `/tmp` or `/name` (Git Bash maps
  those into I:\_Windows\Git).
- Redesign freely: nothing is published, breaking changes are fine.
- Use subagents sparingly and pick the model by difficulty: haiku for simple bulk edits, sonnet for normal
  implementation, opus only for hard design or tricky bugs.
- Generate `.pyi` stubs with `stubpy` (`pip install -e E:\Engineering\Projects\Stubpy` or from PyPI, then
  `stubpy generate svgwriter -o build/stubs` / `stubpy check`) to inspect the public API the way users see it;
  the stubs show whether `**kwargs` chains and overloads read well.
- The PC is shared with other Claude sessions: before long builds or test runs, check `ListAgents` and send
  START/DONE to the session named `Larp master`; if it announced a benchmark, ask and wait.
- Style: inline comments almost none (only *what*, never how/why); short docstrings, NumPy style for public API;
  named constants; split modules at ~300 lines into subpackages; `_`-prefixed modules are package-private;
  `__init__.py` has a docstring with a usage example and a sub-packages list, then `__version__` and
  `__author__ = "Josue N Rivera"`; ruff clean; no mention of other projects or the machine.
- Python 3.10+. Tests with pytest; every feature gets tests.

## Dependencies (decided)
- **Required:** `skia-python` and `numpy` (skia-python already depends on numpy). Remove the "optional skia"
  code paths and `MissingDependencyError`; skia features are always available.
- Nothing else at runtime. ffmpeg stays an optional external program for video.

## Requested changes and features (all from the owner)
1. **Remove `%` / `%=`** for definitions; it is confusing. Definitions go into `<defs>` automatically when a
   shape references them (or via an explicit `doc.define(x)` / `doc.defs += x`).
2. **Geometry model (design carefully, decide what is best and document it in DESIGN.md):**
   - Idea from the owner: treat SVG coordinates as an *anchor* attribute and do all moves via the transform.
     When `anchor` is None it is the centre of the shape / group / image; when set, it is fixed.
   - Every element has `t` (its transform, readable and composable).
   - Every element has `.scale()`, `.rotate()`, `.translate()`, `.skew()` (with a choice of local vs global
     frame), returning self for chaining.
   - Setting `.x`, `.y`, `.cx`, `.width`, ... must stay consistent with the transform/anchor model.
   - Patterns and gradients use the same `t` transform model.
   - Explain in the README what `*` and `@` do (today `shape * T` / `shape @ M` bake a transform into a path;
     reconsider whether that is the clearest meaning).
3. **Paths:** fluent construction `path().move_to(110, 90).line_to(...).curve_to(...).close()` etc.
4. **Conversions on everything, raising a clear error when impossible** (e.g. `image.to_path()`):
   `to_path()` (shapes, text via glyph outlines, groups merged with path ops, clips flattened),
   `to_image()` / `rasterize()` (returns a numpy array), `to_group()`.
5. **Clipping:** `art.clip(circle(...))` works on any element; `.clip()` on all shapes and groups;
   `flatten_clip()` / `to_path()` turns a clipped element into a single path with ops applied.
6. **Path ops (skia PathOps)** for shapes, groups, text and paths: `|` union, `&` intersect, `-` difference,
   `^` xor, plus simplify, stroke-to-path, exact bounds, contains, length, point-at-length.
7. **Constructors don't have to mirror SVG attributes** when an easier representation exists (e.g. colors as
   tuples/names, rect from corners or centre+size, angles in degrees, etc.); SVG output stays correct.
8. **Attribute access:** every SVG property of every element is readable/writable as a Python attribute.
9. **Images:** store pixels as numpy arrays so users can manipulate them directly. Store color channels and
   alpha separately, with alpha always broadcastable to the channels (a fully opaque image stores alpha as the
   scalar 1.0). Decide and document value ranges: normalised floats 0.0–1.0 internally for color/opacity, with
   conversions from/to uint8 and CSS forms.
10. **Document:** auto-size when width/height are not set (confirm it works; there is a root as well, keep the
    model clear); elements accessible by index / id / iteration (`doc[0]`, `doc["logo"]`, `for el in doc`);
    adding objects that implement `_repr_svg_` (e.g. from other libraries) parses and inserts them;
    `_repr_svg_` / `_repr_png_` for notebooks.
11. **Rendering via skia:** `rasterize()` → numpy (RGBA), PNG/JPEG/WebP/PDF export; animation export via
    ffmpeg (keep `render_animation` and the CLI).
12. **Pluggable exporters/importers with a registry** (`svgwriter.export.register(...)`): SVG (with links,
    `<a>`, ids preserved), PNG/JPEG/WebP, PDF (skia), TikZ and/or PGF (decide; at least one), EPS/PS if
    feasible, and anything else useful. Exporters are discoverable by file extension.
13. **Performance:** consider async I/O and threads where they help (batch rasterization, export of many
    documents, frame rendering for animation); measure before adding complexity.
14. Remove web-only bits (already done: no script/foreignObject/cursor/events).
15. Keep animation elements (SMIL) and the ffmpeg-based video export.
16. Fix any IDE deprecation warnings (collections.abc, contextlib.AbstractContextManager; contextmanager itself
    is fine).

## Deliverables
- Working package with the above, a clear README (usage-first, concise feature table), docs-quality
  docstrings on the public API, examples, and a full test suite (aim for broad coverage; skia features are
  always tested now).
- `DESIGN.md` updated with the geometry/transform model and every API decision.
- `ROADMAP.md` with Done / Later.
- When a milestone is complete, stop and tell the owner what is ready to commit.
