# Extending svgwriter

Everything svgwriter finds by name lives in a registry, and every registry works the same way:

| Call | Does |
| --- | --- |
| `@registry.register`, `@registry.register(name=..., replace=True)`, `registry.register(item)` | adds an entry, under its own name unless `name=` is given |
| `registry.list()` | every name, built-in ones first |
| `registry.get(name)` | the entry; an unknown name raises `svg.errors.UnknownNameError` suggesting the closest names |
| `registry.unregister(name)` | removes an entry you added; a built-in you replaced comes back |

A taken name raises `ValueError` naming the function or module that owns it, built-ins included;
`replace=True` replaces one on purpose. `svg.errors.UnknownNameError` is both a `KeyError` and a `ValueError`.

| Registry | Entries | Entry-point group |
| --- | --- | --- |
| `svg.preset.animation` | `f(motion, *, option=default) -> Motion`, reached as `el.animate.<name>` | `svgwriter.animation` |
| `svg.preset.behavior` | `f(element, seconds, *, option=default)`, run by a scene before every frame | `svgwriter.behavior` |
| `svg.preset.shape` | functions returning an element (`svgwriter shapes`) | `svgwriter.shape` |
| `svg.preset.size` | page sizes for `Document(size=...)` | `svgwriter.size` |
| `svg.preset.pattern`, `filter`, `gradient`, `marker` | functions returning that definition, joining `svg.patterns` and the others | `svgwriter.pattern`, ... |
| `svg.preset.effect` | `f(element, *, option=default)` styling any element (`el.effect(name)`) | `svgwriter.effect` |
| `svg.preset.interpolator` | `f(a, b, t) -> value` for a `kind=` or `attribute=`, used by `svg.interpolate`, tweens and morphs | `svgwriter.interpolator` |
| `svg.preset.font` | font families from files, folders or bytes (`svg.preset.font(path, name=None)`), used by measuring, outlines and PNG, PDF and EPS text | `svgwriter.font` (a path, paths, or a function returning them) |
| `svg.themes` | `svg.Theme` instances | `svgwriter.theme` |
| `svg.formats` | `svg.Format` subclasses (one instance each) | `svgwriter.format` |
| `svg.renderers` | `f(document, seconds)` returning PNG bytes or an RGBA array | `svgwriter.renderer` |
| `svg.project.presets` | `svg.project.Preset` starter folders (`svgwriter new --preset`) | `svgwriter.project_preset` |
| `svgwriter` command line | click commands | `svgwriter.command` |

`svg.preset.KINDS` maps each preset kind to its registry.

## Presets

```python
import svgwriter as svg


@svg.preset.animation
def bob(motion: svg.Motion, *, height: float = 8, dur: float = 1) -> svg.Motion:
    return motion.move_by(0, -height, dur / 2).move_by(0, height, dur / 2, begin=dur / 2)


@svg.preset.behavior
def drift(element: svg.Element, seconds: float, *, speed: float = 20) -> None:
    element.matrix = element.home.matrix
    element.translate(speed * seconds, 0)


@svg.preset.shape(name="badge")
def round_badge(cx: float, cy: float, r: float, **kwargs) -> svg.Circle:
    return svg.Circle(cx, cy, r, **kwargs)


svg.preset.size("poster-50x70", "50cm", "70cm")


@svg.preset.pattern
def bricks(*, size: float = 12, color: str = "firebrick") -> svg.Pattern:
    mortar = svg.rect(0, 0, size, size / 2, fill=color, stroke="white")
    return svg.Pattern(mortar, width=size, height=size / 2, pattern_units="userSpaceOnUse")


@svg.preset.effect
def ember(element: svg.Element, *, color: str = "#f97316") -> None:
    element.fill = svg.gradients.blend("#fde68a", color, "#7f1d1d", angle=-90)
    element.filter = svg.filters.glow(3, color=color)


print(svg.Document(size="poster-50x70").root.get("width"))   # the size preset, by name
doc = svg.Document(100, 60)
doc.add(svg.preset.shape.get("badge")(30, 30, 25, fill=svg.patterns.bricks())).effect("ember")
doc[0].animate.bob(height=2)
print(svg.preset.effect.list())


@svg.preset.interpolator(attribute="opacity")
def stepped_opacity(a: float, b: float, t: float) -> float:
    return round(a + (b - a) * t, 1)


faint, solid = svg.circle(10, 10, 5, opacity=0.1), svg.circle(10, 10, 5, opacity=0.9)
print(svg.interpolate(faint, solid, 0.33).get("opacity"))   # blended with stepped_opacity

[brand] = svg.preset.font(svg.Typeface("serif").faces[0].data, name="Brand Serif")
doc.text("Brand", x=5, y=55, font_family=brand)       # measured, outlined and rendered with the file

for kind, name in [("font", "Brand Serif"), ("animation", "bob"), ("behavior", "drift"), ("shape", "badge"), ("size", "poster-50x70"),
                   ("pattern", "bricks"), ("effect", "ember"), ("interpolator", "stepped_opacity")]:
    svg.preset.KINDS[kind].unregister(name)            # tests and notebooks can clean up
```

## Themes

```python
brand = svg.themes.get("light").replace(name="brand", palette={"primary": "#ff6600"})
svg.themes.register(brand)
doc = svg.Document(120, 60, theme="brand")
doc.rect(10, 10, 100, 40, rx=6).as_role("box")          # the brand's primary colour, by role
doc.text("Brand", x=60, y=36, text_anchor="middle", font_size=20).as_role("title")
svg.themes.unregister("brand")
```

## Formats

```python
class Count(svg.Format, name="count", extensions=(".count",), binary=False):
    """The number of top-level elements."""

    def write(self, document, **options):
        return str(len(document))


doc.save("figure.count")
svg.formats.unregister("count")
```

See [Export and import](export.md#your-own-formats) for reading, multi-page formats and lookups.

## Renderers

```python
@svg.renderers.register(name="flat")
def flat(document: svg.Document, seconds: float) -> bytes:
    return document.at(seconds).export("png")


# svgwriter animate scene.py --renderer flat
svg.renderers.unregister("flat")
```

## Project presets

```python
from pathlib import Path

folder = Path("badge-preset")
folder.mkdir(exist_ok=True)
(folder / "README.md").write_text("# {{ project_name }}\n", encoding="utf-8")
svg.project.presets.register(svg.project.Preset("badge", "A round badge", folder, extends="blank"))
svg.project.presets.unregister("badge")
```

## Command-line commands

```python
import click


@click.command(help="Say hello.")
def hello() -> None:
    click.echo("hello from a plugin")
```

## Shipping a plugin package

A package registers entries for everyone who installs it through entry points in its `pyproject.toml`.
Each entry names an object: importing a module whose decorators or class definitions register
themselves is enough (as for presets and formats), and an object that is not registered yet is
registered under the entry's name (as for themes, renderers, project presets and commands).

```toml
[project.entry-points."svgwriter.effect"]
ember = "svgwriter_ember.effects:ember"

[project.entry-points."svgwriter.theme"]
brand = "svgwriter_brand:BRAND"

[project.entry-points."svgwriter.format"]
count = "svgwriter_count:Count"

[project.entry-points."svgwriter.renderer"]
flat = "svgwriter_flat:flat"

[project.entry-points."svgwriter.project_preset"]
badge = "svgwriter_badge:BADGE"

[project.entry-points."svgwriter.command"]
hello = "svgwriter_hello:hello"
```

Entry points load the first time a registry is listed or asked for a name it does not have, so they
cost nothing until then, and a built-in lookup such as `svg.themes.get("dark")` never loads them. A plugin
that fails to import is reported once as a `RuntimeWarning` naming the entry point, and the rest of
svgwriter keeps working.
