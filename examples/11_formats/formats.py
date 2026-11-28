"""# Formats

You will build: one small landscape picture saved as SVG, PNG, PDF, EPS, TikZ, PowerPoint and DXF, then opened again.

Run it from this folder with ``python formats.py``, or open ``formats.ipynb``. Files go to a ``formats`` folder.
"""

import importlib.util
import warnings
from pathlib import Path

import svgwriter as svg

# %% [markdown]
# A small drawing with a gradient, shapes and text. Everything below is saved from this one document.

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
# `doc.save` picks the format from the file name. A PNG turns everything, text included, into pixels.

# %%
formats = Path("formats")
formats.mkdir(exist_ok=True)

doc.save("11_formats.svg")
doc.save(formats / "drawing.svg")
doc.save(formats / "drawing.png", scale=2)
print("svg and png:", ", ".join(sorted(path.name for path in formats.iterdir())))

# %% [markdown]
# ## Text-keeping formats
#
# PDF, EPS and TikZ (for LaTeX documents) keep text as real text you can select and search.

# %%
doc.save(formats / "drawing.pdf")
doc.save(formats / "drawing.eps")
doc.save(formats / "drawing.tikz")
tikz = (formats / "drawing.tikz").read_text(encoding="utf-8")
print("\\node in TikZ:", [line.strip() for line in tikz.splitlines() if "\\node" in line][:1])
print("text in PDF:", b"/Font" in (formats / "drawing.pdf").read_bytes())

# %% [markdown]
# PowerPoint gives editable shapes and text boxes (needs `pip install "pysvgwriter[office]"`).
# DXF is for CAD programs.

# %%
if importlib.util.find_spec("pptx") is not None:
    doc.save(formats / "drawing.pptx")
doc.save(formats / "drawing.dxf")
print(", ".join(sorted(path.name for path in formats.iterdir())))

# %% [markdown]
# ## Reading back
#
# `Document.open` reads the files back. Counting what comes back shows what each format kept.

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
# The PDF opens as a drawing again, ready to edit. Next: [12 Print sizes](../12_print_sizes/print_sizes.py).

# %%
svg.Document.open(formats / "drawing.pdf")
