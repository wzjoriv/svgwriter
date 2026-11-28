"""# Math and diagrams

You will build: a card of famous formulas, a flowchart from a Mermaid file and a whiteboard sketch opened
from Excalidraw.

Run it from this folder with ``python math_and_diagrams.py``, or open ``math_and_diagrams.ipynb``.
"""

import svgwriter as svg

# %% [markdown]
# `svg.latex` turns a LaTeX formula into shapes you can colour, scale and place. For the best results
# install the math extra: `pip install "pysvgwriter[math]"`.

# %%
WIDTH, HEIGHT = 420, 260
FORMULAS = (
    (r"e^{i\pi} + 1 = 0", "#be123c"),
    (r"\int_0^\infty e^{-x^2}\,dx = \frac{\sqrt{\pi}}{2}", "#0f766e"),
    (r"\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}", "#1d4ed8"),
)

formulas = svg.Document(WIDTH, HEIGHT)
formulas.rect(0, 0, WIDTH, HEIGHT, rx=14, fill="#fffbeb")
for index, (source, color) in enumerate(FORMULAS):
    formula = svg.latex(source, display=True).update(fill=color)
    formulas.add(formula.scale(2.1).place(WIDTH / 2, 52 + index * 76))
formulas

# %% [markdown]
# ## Files made elsewhere
#
# `Document.open` reads a Mermaid flowchart, such as `pipeline.mmd` beside this example, with no extra tools.

# %%
flow = svg.Document.open("pipeline.mmd")
flow

# %% [markdown]
# It also reads Excalidraw whiteboard sketches. Like the flowchart, it arrives as ordinary shapes you can
# restyle and save in any format.

# %%
sketch = svg.Document.open("sketch.excalidraw")
sketch

# %% [markdown]
# Save all three. Next: [14 Interop](../14_interop/interop.py) adds charts from other libraries.

# %%
formulas.save("13_math.svg")
flow.save("13_flowchart.svg")
sketch.save("13_sketch.svg")
