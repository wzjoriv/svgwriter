# Installation

```console
$ pip install pysvgwriter
```

The package installs as `pysvgwriter` and imports as `svgwriter`:

```python
import svgwriter as svg
```

svgwriter needs Python 3.10 or newer. It installs [skia-python](https://kyamagu.github.io/skia-python/)
(geometry, text outlines and rendering), numpy (pixels, points and colors as arrays), uharfbuzz (text
shaping), tomlkit (theme files), click (the command line) and
[python-lcms2](https://wzjoriv.github.io/python-lcms2/) (ICC colour profiles through LittleCMS).
Nothing else is needed at runtime.

Optional extras:

- **widget** for {doc}`notebook panels <../guides/widgets>` (`svg.interact`) through ipywidgets:

  ```console
  $ pip install "pysvgwriter[widget]"
  ```

  Controls, sweeps and the controls of `svgwriter preview` work without it.

Optional external program:

- **ffmpeg** on `PATH` for {doc}`video export <../guides/animation>`. Without it, `render_animation` raises
  `FFmpegNotFoundError` before doing any work.

For a development install, see {doc}`../contributing`.
