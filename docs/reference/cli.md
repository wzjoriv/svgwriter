# Command line

`svgwriter` (also `python -m svgwriter`) is a [click](https://click.palletsprojects.com) group that runs these commands; `svgwriter COMMAND --help` lists the
options of each. Errors are one line on stderr; the exit status is 0 on success, 1 when a command
fails (no scene, ffmpeg missing) and 2 for a usage error, an unreadable file or an invalid project.

| Command | What it does |
|---|---|
| `new [NAME] [--preset P] [--notebook/--script] [--theme T] [--size S]` | Create a project folder from a preset; in a terminal, what the flags leave out is asked with arrow keys (`pysvgwriter[cli]`) or a numbered preset menu; elsewhere the preset's defaults apply |
| `build [--format F ...] [--path DIR]` | Write the project's outputs (all of `[outputs] formats`, or the ones given) |
| `preview [--port N] [--no-open] [--path DIR]` | Serve the outputs on a local page that rebuilds and reloads on save |
| `presets` | List project presets |
| `sizes` | List named canvas sizes (`svg.preset.size.list()`) |
| `shapes`, `elements` | List shape presets and element classes |
| `draw SHAPE [--size N] [--fill C] [-o FILE]` | Write a shape preset as SVG |
| `format INPUT [-o FILE] [--compact] [--precision N]` | Parse an SVG file and write it back out |
| `info INPUT` | Count the elements of an SVG file |
| `animate SCENE [NAMES ...] [--format F] [--fps N] [-o FILE]` | Render scenes through ffmpeg |
| `render SCENE [NAMES ...] [--at SECONDS] [--scale S] [-o FILE]` | Rasterize scenes or an SVG file to PNG |
| `outline TEXT [--font F] [--size N] [-o FILE]` | Write text as glyph outlines |

Packages add commands through the `svgwriter.command` entry-point group, and `COMMANDS.register(command)`
adds one at run time (see [Extending svgwriter](../guides/extending.md)).

```{eval-rst}
.. autodata:: svgwriter.tools.cli.app
   :no-value:
.. autofunction:: svgwriter.tools.cli.main
.. autodata:: svgwriter.tools.cli.COMMANDS
   :no-value:
```
