---
orphan: true
---

# Logos and icons

Keep a logo as a Python function with variants and generate every asset from it. Output is deterministic,
so regenerating and comparing bytes tells whether checked-in assets are stale.

```python
import svgwriter as svg

def logo(theme: svg.Theme | str = "light") -> svg.Document:
    palette = svg.Theme.of(theme).palette
    doc = svg.Document(root=svg.Svg(view_box=(-50, -50, 100, 100)))
    doc.rect(-50, -50, 100, 100, rx=22, fill=palette.primary)
    doc.path(fill="none", stroke=palette.on_primary, stroke_width=12).move_to(-22, 18).line_to(0, -24).line_to(22, 18)
    return doc

light = logo()
for size in (16, 32, 64, 256):
    light.save(f"logo-{size}.png", pixels=size, padding=4)
light.save("favicon.ico", sizes=(16, 32, 48))
light.save("logo.icns")
logo("dark").save("logo-dark.svg")
```

Variants are themes ([Themes](themes.md)): `logo("dark")`, `logo("mono")`, or any
`svg.themes.get("light").replace(palette={...})`. `examples/20_logo/logo.py` in the repository is a complete version with light, dark and mono variants and the full
asset set.
