# Logos and icons

Keep a logo as a Python function with variants and generate every asset from it. Output is deterministic,
so regenerating and comparing bytes tells whether checked-in assets are stale.

```python
import svgwriter as svg

def logo(theme="light"):
    ground, mark = ("#0f766e", "white") if theme == "light" else ("#99f6e4", "#042f2e")
    doc = svg.Document(root=svg.Svg(view_box=(-50, -50, 100, 100)))
    doc.rect(-50, -50, 100, 100, rx=22, fill=ground)
    doc.path(fill="none", stroke=mark, stroke_width=12).move_to(-22, 18).line_to(0, -24).line_to(22, 18)
    return doc

light = logo()
for size in (16, 32, 64, 256):
    light.save(f"logo-{size}.png", size=size, padding=4)
light.save("favicon.ico", sizes=(16, 32, 48))
light.save("logo.icns")
logo("dark").save("logo-dark.svg")
```

`examples/12_logo.py` in the repository is a complete version with light, dark and mono variants and the full
asset set.
