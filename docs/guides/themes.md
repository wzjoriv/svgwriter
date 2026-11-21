# Themes

A theme is a palette, fonts and the styles of named *roles*. Elements say what they are
(`as_role("box")`, `as_role("title")`) rather than which colors they use, and the document's theme
decides how each role looks. Changing the theme restyles the whole drawing.

```python
import svgwriter as svg

doc = svg.Document(240, 100, theme="dark")
doc.rect(0, 0, 240, 100).as_role("background")
doc.text("Results", x=16, y=34).as_role("title")
doc.rect(16, 50, 90, 34, rx=6).as_role("box")
doc += svg.builder.star(200, 60, 20, 8)          # builder shapes carry roles already
doc += svg.builder.arrow(110, 67, 160, 67)

doc.theme = "paper"                               # restyle everything
print(doc.to_string()[:200])
```

## Roles in the output

The SVG gets one `<style id="svgwriter-theme">` holding a `.role-<name>` rule for each role in use
(`arrow.head` becomes `.role-arrow-head`), and elements get the matching class. Nothing else changes, so
the file stays portable: browsers, editors and every svgwriter renderer and exporter (PNG, PDF, EPS,
PowerPoint, ...) resolve the sheet. A themed file read back with `Document.open` keeps its sheet; setting
`doc.theme` replaces the rules on output.

Role rules override plain attributes, as CSS rules do. `as_role` moves the presentation attributes already
on an element into its inline `style`, so values given when the element is made still win:

```python
import svgwriter as svg

warn = svg.rect(0, 0, 40, 20, stroke="red").as_role("box")   # fill from the theme, stroke red
print(warn.style["stroke"], warn.classes)
```

Builder presets work the same way: `svg.builder.star(..., fill="gold")` keeps its gold fill and takes the
rest of the `shape` role.

## Standard roles

| Role | Look |
| --- | --- |
| `background`, `surface` | filled with `background` / `surface` |
| `box` | `surface` fill, thin `border` stroke |
| `shape`, `accent` | filled with `primary` / `accent` (registered builder shapes default to `shape`) |
| `shadow` | filled with `shadow`; draw it offset behind a shape |
| `outline`, `grid` | unfilled, thin `border` stroke |
| `line` | unfilled, `primary` stroke |
| `arrow.line`, `arrow.head` | `foreground` stroke / fill |
| `dot` | filled with `accent`, thin `primary` ring |
| `text`, `code` | `foreground` text |
| `title` | bold `primary` text |
| `subtitle`, `caption` | `muted` text |
| `label` | bold `on_primary` text, for text on a `shape` |
| `success`, `warning`, `error` | filled with the status colors |

## Built-in themes

| Theme | Character |
| --- | --- |
| `light` | the default: slate text, teal titles and shapes, amber dots |
| `dark` | light text on near-black, mint titles |
| `paper` | warm cream ground, brown ink |
| `print` | for papers: serif fonts, dark grey text, ink-blue emphasis, orange second colour, no shadow |
| `mono` | black and white only, black borders and hard shadows |
| `noir` | dark paper: warm off-white on charcoal, pale blue accent, faint light shadow |
| `brutalist` | yellow ground, black 2px borders and hard shadows, electric blue, heavy weights |
| `dracula`, `alucard` | the Dracula palette, dark and light |
| `one-dark`, `one-light` | the One palettes, dark and light |

Body and caption text in every built-in theme meets WCAG AA contrast (4.5:1) against both `background`
and `surface`; titles, which are large, meet 3:1. `svg.Theme.get(name)` returns one;
`svg.THEMES.names()` lists them, and `svg.THEMES.add(name, theme)` registers your own.

`dracula` and `alucard` follow the Dracula palette (MIT licensed, draculatheme.com); `one-dark` and
`one-light` follow Atom's One Dark and One Light themes (MIT licensed). Where an official comment grey is
too faint for caption text, the theme uses a lighter grey from the same palette.

Palette roles: `background`, `foreground`, `surface`, `border`, `muted`, `primary`, `on_primary` (ink on
`primary`), `secondary`, `accent`, `success`, `warning`, `error`, `shadow`. `border` and `muted` are mixed from
`foreground` and `background` unless given, and `shadow` is a translucent `foreground`.

## Variants

Themes are immutable. `replace` builds a variant: palette entries, font values and role properties merge
into the original. Palette entries can be functions of the palette and role values functions of the
theme, written with the typed `Color` methods (`lighten`, `darken`, `mix`, `with_alpha`), so derived values
follow their sources:

```python
import svgwriter as svg

brand = svg.Theme.get("light").replace(
    name="brand",
    palette={"primary": "#7c3aed", "border": lambda p: p.primary.mix(p.background, 0.6)},
    fonts={"family": "Georgia, serif", "sizes": {"title": 28}},
    roles={
        "box": {"stroke-width": 2},                                  # merged into the existing box role
        "badge": lambda t: {"fill": t.palette.accent, "stroke": t.palette.primary},  # a new role
    },
)
print(brand.style("box"), brand.style("badge"))
```

A role value may also be a reference, `"{palette.primary}"` or `"{fonts.sizes.title}"`, alone or inside
text (`"1px solid {palette.border}"`). Unknown roles and references and reference cycles raise
`svg.theme.ThemeError` with the path of the value.

## Using a theme

- `svg.Document(theme=...)` takes a `Theme` or a registered name; `doc.theme` reads or changes it.
- `with theme:` makes a theme the default for documents created in the block. It is a context variable,
  so threads and async tasks each keep their own; outside any block the default is `light`.
- `theme.style(role)` gives a role's resolved `Style`, for elements styled inline instead of by class;
  `theme.palette.primary` gives a single color.

```python
import svgwriter as svg

with svg.Theme.get("print"):
    figure = svg.Document(100, 40)
    figure.text("Figure 1", x=4, y=24).as_role("caption")
print(figure.theme.name, svg.Theme.current().name)
```

## Theme files

`theme.save(path)` writes TOML and `svg.Theme.load(path)` reads it. A file extends a registered theme
(`light` unless `extends` says otherwise) and holds only literals and references; nothing in it runs.

```toml
name = "night"
extends = "dark"

[palette]
primary = "#38bdf8"
accent = "{palette.primary}"

[fonts.sizes]
title = 26

[roles.title]
fill = "{palette.primary}"

[roles."arrow.head"]
fill = "{palette.accent}"
```

Saving writes every value resolved, so a saved file is a snapshot: entries that were functions are
written as the colors they produced. Reading TOML on Python 3.10 needs `tomli`.
