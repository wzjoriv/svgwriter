# Command line

`svgwriter` (also `python -m svgwriter`) is a [click](https://click.palletsprojects.com) group that runs these commands; `svgwriter COMMAND --help` lists the
options of each. Errors are one line on stderr; the exit status is 0 on success, 1 when a command
fails (no scene, ffmpeg missing) and 2 for a usage error, an unreadable file or an invalid project.

| Command | What it does |
|---|---|
| `new [NAME] [--preset P] [--notebook/--script] [--theme T] [--size S]` | Create a project folder from a preset; in a terminal, what the flags leave out is asked with arrow keys (`pysvgwriter[cli]`) or a numbered preset menu; elsewhere the preset's defaults apply |
| `build [--format F ...] [--path DIR]` | Write the project's outputs (all of `[outputs] formats`, or the ones given) |
| `preview [--port N] [--open/--no-open] [--path DIR]` | Serve a live page that redraws as controls move and files change |
| `presets` | List project presets |
| `sizes` | List named canvas sizes (`svg.preset.list("size")`) |
| `shapes`, `elements` | List shape presets and element classes |
| `draw SHAPE [--size N] [--fill C] [-o FILE]` | Write a shape preset as SVG |
| `format INPUT [-o FILE] [--compact] [--precision N]` | Parse an SVG file and write it back out |
| `info INPUT` | Count the elements of an SVG file |
| `animate SCENE [NAMES ...] [--format F] [--fps N] [-o FILE]` | Render scenes through ffmpeg |
| `render SCENE [NAMES ...] [--at SECONDS] [--scale S] [-o FILE]` | Rasterize scenes or an SVG file to PNG |
| `outline TEXT [--font F] [--size N] [-o FILE]` | Write text as glyph outlines |
| `doctor [--json]` | Show what works on this machine, what is missing and how to install it on this OS |

## `svgwriter doctor`

`svgwriter doctor` checks the optional libraries (skia, harfbuzz, lcms2, fontTools, ipywidgets,
matplotlib, ...) and external programs (ffmpeg, LaTeX with dvisvgm, the Mermaid CLI, Graphviz, PlantUML,
D2, Inkscape), and prints one line for each: its version when present, otherwise what it is for and the
command that installs it on this OS and Linux distribution (`apt`, `dnf`, `pacman`, `zypper`, `brew` or
`winget`). The last line counts the installed font families and names what `sans-serif`, `serif`,
`monospace` and emoji resolve to; on Linux with few fonts or no emoji font it adds the distribution's
font packages.

```console
$ svgwriter doctor
svgwriter 2.4.0 on Python 3.13.3, Windows 11 (windows, winget)
  ok   skia         144.1
  ok   harfbuzz     0.57.0
  ...
  --   graphviz     missing (Graphviz DOT diagrams): winget install Graphviz.Graphviz
fonts: 326 families; sans-serif -> Arial, serif -> Times New Roman, monospace -> Consolas, emoji -> Segoe UI Emoji
```

`--json` prints the same report as JSON (`python`, `system`, `system_packages`, `capabilities`,
`fonts`). From Python, `svg.capabilities()` returns the capability part as a read-only mapping of name
to a record with `available`, `version`, `path`, `purpose` and `hint`; it is checked once and cached
(`svg.capabilities(refresh=True)` checks again).

Each program can also be named by an environment variable, `SVGWRITER_<NAME>` (`SVGWRITER_FFMPEG`,
`SVGWRITER_DOT`, `SVGWRITER_MMDC`, `SVGWRITER_LATEX`, `SVGWRITER_DVISVGM`, ...), which wins over `PATH`.

```{eval-rst}
.. autodata:: svgwriter.tools.cli.app
   :no-value:
.. autofunction:: svgwriter.tools.cli.main
.. autofunction:: svgwriter.capabilities
```
