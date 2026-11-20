# Installation

```console
$ pip install pysvgwriter
```

The package installs as `pysvgwriter` and imports as `svgwriter`:

```python
import svgwriter as svg
```

svgwriter needs Python 3.10 or newer. It installs [skia-python](https://kyamagu.github.io/skia-python/)
(geometry, text outlines and rendering), numpy (pixels, points and colors as arrays) and uharfbuzz (text
shaping). Nothing else is needed at runtime.

Optional external program:

- **ffmpeg** on `PATH` for {doc}`video export <../guides/animation>`. Without it, `render_animation` raises
  `FFmpegNotFoundError` before doing any work.

For development:

```console
$ pip install -e ".[dev,test]"
$ python scripts/dev.py test          # tests
$ python scripts/dev.py check         # lint, tests, docs
$ python scripts/dev.py docs          # build these docs
```
