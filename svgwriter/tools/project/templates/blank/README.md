# {{ project_name }}

A design made with [svgwriter](https://github.com/wzjoriv/svgwriter), started from the `{{ preset }}` preset.

```
svgwriter preview    # a browser page that rebuilds and reloads on every save
svgwriter build      # writes every output listed in svgwriter.toml into output/
```

## Layout

| Path | What it holds |
|---|---|
| `svgwriter.toml` | Size, theme, entry and outputs |
| `main.py` (or `main.ipynb`) | The drawing |
| `theme.toml` | Palette, fonts and role styles; extends a built-in theme |
| `components/` | Reusable pieces: functions that return groups |
| `animations/` | Animation presets of this project (`@svg.preset.animation`) |
| `assets/fonts/` | Font files, registered before every build |
| `assets/images/`, `assets/data/` | Pictures and data the drawing reads |
| `output/` | Build results (not committed) |

## Changing it

- Colors and fonts: edit `theme.toml`. Values starting with `=` are expressions, such as
  `on_primary = "=readable({palette.primary})"`.
- Size and outputs: edit `svgwriter.toml`; `svgwriter sizes` lists the named sizes, and
  `svgwriter build --format pdf` writes one format.
- Fonts: drop `.ttf` or `.otf` files into `assets/fonts/` and use their family name in `theme.toml`.
- Motion: add a function to `animations/`, decorate it with `@svg.preset.animation`, and call it with
  `element.animate.apply(fn, ...)` or by name, `element.animate.<name>(...)`.
