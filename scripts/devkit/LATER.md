# LATER (planned devkit tools, not built yet)

## logo
A project describes its logo once, in Python, with `svgwriter`; devkit renders every asset from it.

```toml
[tool.devkit.logo]
source = "assets/logo.py"        # defines `logo()` returning an svgwriter Document (or a module-level `logo`)
out = "assets/logo"              # output folder
svg = ["logo.svg", "logo-mono.svg"]          # vector outputs (variants passed as keyword args to logo())
png = [16, 32, 48, 64, 128, 256, 512, 1024]  # square PNG sizes
ico = [16, 32, 48, 256]          # sizes packed into logo.ico (Windows / favicon)
icns = true                      # macOS logo.icns
favicon = true                   # favicon.ico + apple-touch-icon.png + site.webmanifest icons
docs = "docs/_static"            # also copy logo.svg / favicon.ico for Sphinx (html_logo / html_favicon)
```

Commands: `dev.py logo build` (write everything), `dev.py logo check` (exit 1 when outputs are stale against
the source; for CI), `dev.py logo show` (open a preview).

Needs from svgwriter: rasterize to numpy/PNG at any size (skia), exact-size viewBox fitting, variant parameters
(dark / light / monochrome), ICO / ICNS writers (or devkit packs PNGs itself), deterministic output for `check`.

### svgwriter API available for it (svgwriter branch v2-redesign)
- Source convention: `logo(theme="light"|"dark", *, mono=False) -> Document` (see svgwriter `examples/logo.py`).
- Exact sizes: `doc.rasterize(size=(w, h), padding=p)` -> numpy; `doc.save("x.png", size=64, padding=4)`.
- Icons: `doc.export("ico", sizes=(16, 32, 48), padding=p)`, `doc.export("icns", sizes=...)`.
- Raw PNG bytes: `svgwriter.ops.encode(doc.rasterize(size=(s, s)))`.
- Output is byte-deterministic for svg/png/webp/jpeg/pdf/ico/icns, so `logo check` can regenerate and compare.
- Extra formats (e.g. webmanifest) can register with `svgwriter.export`.
