# Projects

A project is a folder for one design: the code that draws it, its theme, its assets and the files it
builds. `svgwriter new` starts one from a preset, `svgwriter build` writes every output, and
`svgwriter preview` shows them in a browser page that rebuilds and reloads whenever you save.

```console
svgwriter new my-poster --preset poster
cd my-poster
svgwriter preview      # browser page that refreshes on save (Ctrl+C stops)
svgwriter build        # writes every output listed in svgwriter.toml into output/
svgwriter presets      # the presets, one line each
```

Without `--preset`, `svgwriter new` asks in a terminal. With the optional `cli` extra
(`pip install "pysvgwriter[cli]"`) it uses arrow-key prompts for the preset (each with its description),
script or notebook, theme, page size (common names or a custom width and height) and the project name when
`NAME` is left out; without it, a numbered menu picks the preset. Flags skip their prompts, and input that
is not a terminal never prompts, so scripts stay non-interactive:

```console
svgwriter new my-poster --preset poster --theme dracula --size a3
svgwriter new my-deck --preset slides --notebook --size 1920,1080
```

`--theme` names a built-in theme that `theme.toml` extends, and `--size` a size name or `WIDTH,HEIGHT`
(numbers or lengths such as `50cm,70cm`) written to `svgwriter.toml`; both default to the preset's own.
The same steps from Python:

```python
import svgwriter as svg

project = svg.Project.new("my-poster", preset="poster", theme="dracula", size="a3")   # svgwriter new my-poster --preset poster --theme dracula --size a3
print([path.name for path in project.build()])             # svgwriter build
print([path.name for path in project.build(["png"])])      # svgwriter build --format png
```

## Layout

```text
my-poster/
├─ svgwriter.toml      project settings: entry, size, theme, outputs
├─ main.py             the drawing: def build(doc) -> None
├─ theme.toml          palette, fonts and roles; extends a built-in theme
├─ components/         reusable pieces: functions that return groups
│  ├─ __init__.py
│  └─ title_block.py
├─ animations/         animation presets of this project (@svg.preset.animation)
│  ├─ __init__.py
│  └─ bob.py
├─ assets/
│  ├─ fonts/           registered before every build
│  ├─ images/
│  └─ data/            csv or json the drawing reads
├─ output/             build results (git-ignored)
├─ README.md
└─ .gitignore
```

`build(doc)` receives an empty document with the project's size and theme already set, so it holds only
drawing code. Builds run in the project folder, so relative paths such as `assets/data/values.csv` work,
and modules the project imports (`components`, `animations`) are imported fresh on every build: the
preview always shows the files as they are now.

## svgwriter.toml

```toml
[project]
name = "my-poster"          # output files are named after it; defaults to the folder name
entry = "main:build"        # module:object; also "main.ipynb:build"
size = "a4"                 # a size name (`svgwriter sizes`) or [width, height], e.g. ["50cm", "70cm"]
theme = "theme.toml"        # a theme file in the project, or a built-in theme name such as "dark"
fonts = "assets/fonts"      # folder whose .ttf/.otf/.ttc files are registered

[outputs]
formats = ["pdf", "svg", "png"]
directory = "output"
png = { dpi = 150 }         # options for one format, passed to its exporter
gif = { fps = 12, scale = 0.5 }
```

| Key | Default | Meaning |
|---|---|---|
| `project.name` | folder name | The project name; outputs are `output/<name>.<ext>` |
| `project.entry` | `"main:build"` | What draws the project (see below) |
| `project.size` | none (fits the content) | A [named size](export-import.md#page-sizes) or `[width, height]`; `ProjectConfig(size=svg.size.a4)` takes a `PageSize` |
| `project.theme` | none | A theme file or a registered theme name |
| `project.fonts` | `"assets/fonts"` | Font folder |
| `outputs.formats` | `["svg", "png"]` | Any export format name, plus `gif`, `mp4`, `webm`, `mov` for animations |
| `outputs.directory` | `"output"` | Where outputs go |
| `outputs.<format>` | none | Exporter options for that format, such as `png = { scale = 2 }` |

An unknown key or a bad value stops the build with the file and the key in the message. Teams that
already keep a `pyproject.toml` can put the same tables under `[tool.svgwriter]` instead:

```toml
[tool.svgwriter.project]
entry = "design.main:build"
size = "letter"

[tool.svgwriter.outputs]
formats = ["pdf"]
```

`svgwriter.toml` comes first; otherwise the nearest `pyproject.toml` with a `[tool.svgwriter]` table, in
the folder or above it. svgwriter never reads either file by itself: importing the library or creating a
document stays free of hidden configuration, and only `Project.load()` and the `svgwriter build` and
`svgwriter preview` commands look for them.

## Entries and outputs

The entry object decides what gets drawn:

| Entry object | Outputs |
|---|---|
| A function taking a `Document` | One page: `output/<name>.<ext>` per format |
| A list of such functions | One page each: one PDF or PowerPoint file, numbered files for other formats |
| A `Scene` class (or a list) | GIF frames rendered in Python (no ffmpeg), animated SVG and PowerPoint with `update` and behaviours baked into SMIL, `mp4`/`webm`/`mov` through ffmpeg |

Still formats such as PDF and PNG show a page once its animations have ended; `png = { seconds = 0 }`
shows the start instead. SVG, GIF and PowerPoint keep the animations.

## Presets

| Preset | Starts as | Outputs |
|---|---|---|
| `blank` | an 800 x 600 canvas with a title component and a bobbing star | svg, png |
| `poster` | an A4 page drawn in millimetres, a bar chart from `assets/data/values.csv` | pdf, svg, png |
| `slides` | a 16:9 deck, one function per slide, items that fade in one by one | pptx, pdf |
| `animation` | a `Scene` class with staggered presets and a bar grown in `update` | gif, svg |

Every preset builds out of the box. Presets are a registry, so a team can ship its own starter folder;
`extends=` lays it over another preset, so the folder only holds what differs:

```python
import pathlib

folder = pathlib.Path("badge-preset")
folder.mkdir()
(folder / "svgwriter.toml").write_text('[project]\nname = "{{ project_name }}"\nsize = "icon"\n'
                                       '[outputs]\nformats = ["svg", "png"]\n', encoding="utf-8")
svg.project.presets.register(svg.project.Preset("badge", "A 512 x 512 app icon", folder, extends="blank"))
print(svg.project.presets.list())
svg.project.presets.unregister("badge")
```

In a preset folder, a `-tpl` suffix is dropped from file names (`main.py-tpl` becomes `main.py`, so the
templates are not importable modules), a `dot-` prefix becomes a dot (`dot-gitignore`), and
`{{ project_name }}` and `{{ preset }}` are replaced in text files.

## Notebook projects

`svgwriter new NAME --notebook` writes `main.ipynb` instead of `main.py`, with the same cells and two
more at the end:

```python
# project = svg.Project.load()
# project.preview()      # every output inline; GIFs and SVG animations play
```

Inside the notebook, `project.build()` and `project.preview()` use the notebook's own `build` (or scene
classes), so there is nothing to save first. `svgwriter build` and the live preview run the notebook in
a fresh kernel and build there, so the command line and the notebook write the same files. Running a
notebook needs the `notebook` extra: `pip install pysvgwriter[notebook]`.

`project.preview()` works for any project: it builds the outputs and shows each one, with PDF pages and
PowerPoint slides read back as drawings.

## Animations and components of your own

The `animations/` folder holds animation presets made with `@svg.preset.animation` (see
[the animation guide](animation.md#presets-of-your-own)); importing the package registers them, so
`element.animate.bob()` works anywhere in the project, and `element.animate.apply(bob, height=8)` calls
one with typed options. `components/` holds plain functions that return groups, styled by theme roles
so they follow `theme.toml`.

## Live preview

`svgwriter preview` serves `http://127.0.0.1:8000/` (`--port` to change it, `--no-open` to skip the
browser). It polls the project's files twice a second; when one changes it rebuilds, and the page
reloads itself. A failed build shows its traceback under the last outputs that worked until the next
save fixes it. It uses only the standard library.

An entry that declares controls with `@svg.widgets.controls` gets a form above the outputs: sliders,
buttons, colour pickers and switches as plain HTML inputs. Each change rebuilds the project with the new
values and swaps the outputs in place; `svgwriter build` uses the starting values. See {doc}`widgets`.
