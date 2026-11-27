# Projects

A project is a folder for one design: the code that draws it, its theme, its assets and the files it
builds. `svgwriter new` starts one from a preset, `svgwriter build` writes every output, and
`svgwriter preview` shows them on a live browser page that redraws as you move its controls or save a file.

```console
svgwriter new my-poster --preset poster
cd my-poster
svgwriter preview      # live page: redraws on every control change and save (Ctrl+C stops)
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

A `[preview]` table configures `svgwriter preview`; see [Live preview](#live-preview).

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

`svgwriter preview` serves `http://127.0.0.1:8000/` and opens it in a browser (`--port` and
`--open/--no-open` override the manifest). The page shows the drawing large at the top, with a tab per
page or scene when there are several, and the controls the entry declares with `@svg.widgets.controls` in
a panel: on the right in wide windows, below the drawing in narrow or portrait ones. It uses only the
standard library and plain HTML, follows the system's light or dark mode, and every control works from the
keyboard.

Moving a control redraws only what the page shows, in memory: each page as SVG, each scene as animated SVG
with its behaviors baked into SMIL. No output file is written, so a slider tick costs one drawing, not a
build. The page waits for a short pause in the input (`debounce_ms`) and keeps only the newest request:
values that arrive while a drawing runs are merged, the latest win, and a stale answer is dropped. The
status line under the drawing gives the time each drawing took; an error shows its traceback there too,
under the last drawing that worked, until a change fixes it.

The project's code is imported once and reused for every control change. Saving a file imports it again,
so edits always show, and the page updates without a reload. Once the project has been quiet for a second
after a save, the output files are written as `svgwriter build` writes them; the **Export** button
in the header writes them on demand, with the current control values. `svgwriter build` uses the
controls' starting values. See {doc}`widgets`.

```toml
[preview]
pages = ["cover", "cover-Intro"]   # which pages and scenes to show, in this order
background = "checker"            # "checker", "light", "dark" or a colour such as "#20242c"
layout = "auto"                   # controls on the "right", at the "bottom", or "auto"
fit = "contain"                   # scale the drawing to its area, or "actual" size
port = 8000
open = true                       # open a browser on start
debounce_ms = 80                  # pause after a control moves before drawing
build_on_save = true              # write the outputs after a save
formats_on_build = ["svg"]        # what saves and Export write
```

| Key | Default | Meaning |
|---|---|---|
| `preview.pages` | all | Names of the pages and scenes to show, in order: the output name without its extension (`card`, `card-2`, `card-Sweep`) |
| `preview.background` | `"checker"` | Behind the drawing: `"checker"`, `"light"`, `"dark"` or a colour |
| `preview.layout` | `"auto"` | Controls on the `"right"`, at the `"bottom"`, or `"auto"`: right when the window is wide, bottom otherwise |
| `preview.fit` | `"contain"` | `"contain"` scales the drawing to its area, keeping its proportions; `"actual"` shows it at its own size |
| `preview.port` | `8000` | The local port |
| `preview.open` | `true` | Open the page in a browser on start |
| `preview.debounce_ms` | `80` | Milliseconds the page waits after a control moves |
| `preview.build_on_save` | `true` | Write the output files after a save |
| `preview.formats_on_build` | `outputs.formats` | The formats that saves and the Export button write |

In a `pyproject.toml` the table is `[tool.svgwriter.preview]`.
