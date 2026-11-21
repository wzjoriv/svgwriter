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
shaping) and tomlkit (theme files). Nothing else is needed at runtime.

Optional extras:

- **color** for ICC colour profiles: `<color-profile>`, `icc-color(...)` paints and images with
  embedded or assigned profiles are converted to sRGB through LittleCMS
  ([python-lcms2](https://wzjoriv.github.io/python-lcms2/)):

  ```console
  $ pip install "pysvgwriter[color]"
  ```

  Without it, `icc-color(...)` draws its sRGB fallback colour and images are drawn as their decoder
  delivers them; a one-time warning says profiles were skipped.

- **widget** for {doc}`notebook panels <../guides/widgets>` (`svg.interact`) through ipywidgets:

  ```console
  $ pip install "pysvgwriter[widget]"
  ```

  Controls, sweeps and the controls of `svgwriter preview` work without it.

Optional external program:

- **ffmpeg** on `PATH` for {doc}`video export <../guides/animation>`. Without it, `render_animation` raises
  `FFmpegNotFoundError` before doing any work.

For a development install, see {doc}`../contributing`.
