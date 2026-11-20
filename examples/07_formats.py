"""Step 7: one drawing exported to many formats and read back.

``doc.save(path)`` picks the exporter from the extension and ``Document.open(path)`` the importer, so the
same drawing travels through vector, raster, document, TeX and CAD files.
Run it as ``python 07_formats.py`` or open ``07_formats.ipynb`` to see each step.
"""

import importlib.util
import os
import tempfile
import warnings
from pathlib import Path

import svgwriter as svg

# %% [markdown]
# A small drawing with a gradient, a shape, a polyline and a line of text. Everything below is
# written from this one `Document`.

# %%
WIDTH, HEIGHT = 320, 180
doc = svg.Document(WIDTH, HEIGHT)
doc.title("Formats")
doc.rect(0, 0, WIDTH, HEIGHT, rx=12, fill=svg.LinearGradient.vertical("#e0f2fe", "#bae6fd"))
doc.circle(80, 95, 46, fill="#f59e0b", stroke="#92400e", stroke_width=3)
doc.polygon([(150, 140), (210, 50), (270, 140)], fill="#10b981", stroke="#065f46", stroke_width=3)
doc.polyline([(20, 160), (90, 150), (160, 165), (300, 150)], fill="none", stroke="#1e3a8a", stroke_width=2)
doc.text("export me", x=WIDTH / 2, y=32, font_size=24, font_family="Arial, Helvetica, sans-serif",
         font_weight="bold", text_anchor="middle", fill="#0f172a")
doc

# %% [markdown]
# Save SVG and PNG. Set `SVGWRITER_EXAMPLES_OUT` to choose the folder. A PNG is pixels, so text becomes
# pixels too; the SVG keeps it as text.

# %%
out = Path(os.environ.get("SVGWRITER_EXAMPLES_OUT") or tempfile.mkdtemp(prefix="svgwriter-"))
out.mkdir(parents=True, exist_ok=True)
formats = out / "formats"
formats.mkdir(exist_ok=True)

doc.save(out / "07_formats.svg")
doc.save(formats / "drawing.svg")
doc.save(formats / "drawing.png", scale=2)
print("svg and png:", ", ".join(sorted(path.name for path in formats.iterdir())))

# %% [markdown]
# PDF, EPS and TikZ keep text as text, so it stays selectable in a viewer or searchable in the source.
# The TikZ file is a `tikzpicture` of `\draw` and `\node` commands; `standalone=True` makes it compilable.

# %%
doc.save(formats / "drawing.pdf")
doc.save(formats / "drawing.eps")
doc.save(formats / "drawing.tikz")
tikz = (formats / "drawing.tikz").read_text(encoding="utf-8")
print("\\node in TikZ:", [line.strip() for line in tikz.splitlines() if "\\node" in line][:1])
print("text in PDF:", b"/Font" in (formats / "drawing.pdf").read_bytes())

# %% [markdown]
# PowerPoint (editable shapes and text boxes, needs `pysvgwriter[office]`) and DXF (CAD polylines in
# millimetres, one layer per colour). Exporters that need an optional package are skipped when it is missing.

# %%
if importlib.util.find_spec("pptx") is not None:
    doc.save(formats / "drawing.pptx")
doc.save(formats / "drawing.dxf")
print(", ".join(sorted(path.name for path in formats.iterdir())))

# %% [markdown]
# `Document.open` reads files back (TikZ is shown above as source). Text-keeping formats return `<text>`
# elements again, DXF returns polylines only and PNG a single `<image>`. Counting elements of each kind
# shows what every format preserved.

# %%
rows = []
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for path in sorted(formats.iterdir()):
        if path.suffix == ".tikz":
            continue
        back = svg.Document.open(path)
        texts = back.root.find_all("text")
        shapes = sum(len(back.root.find_all(tag)) for tag in ("path", "polygon", "polyline", "rect", "circle", "line"))
        images = len(back.root.find_all("image"))
        rows.append((path.name, len(texts), shapes, images))
for name, texts, shapes, images in rows:
    print(f"{name:14} text={texts:<3} shapes={shapes:<4} images={images}")

# %% [markdown]
# The PDF read back is a drawing again: shapes, a gradient and the text, ready to edit and save as SVG.

# %%
svg.Document.open(formats / "drawing.pdf")
