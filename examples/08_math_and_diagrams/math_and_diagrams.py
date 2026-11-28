"""# Math and diagrams

LaTeX formulas and a Mermaid flowchart, both drawn without any tool beyond Python.

Run it as ``python 08_math_and_diagrams.py`` or open ``08_math_and_diagrams.ipynb`` to see each step.
"""

import svgwriter as svg

# %% [markdown]
# `svg.latex` typesets a formula as vector outlines (a group of paths). It uses TeX when `latex` and
# `dvisvgm` are installed, otherwise Ziamath (`pip install "pysvgwriter[math]"`) and then matplotlib's mathtext.
# The result is an ordinary element: scale, colour, place and export it like any other.

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
# `Document.open` reads Mermaid files such as `pipeline.mmd`, beside this example
# (`Document.from_string(text, "mermaid")` reads source text).
# Flowcharts (`graph` / `flowchart`) are parsed and laid out by svgwriter itself when the Mermaid CLI
# is missing, so this needs no external tool.

# %%
flow = svg.Document.open("pipeline.mmd")
flow

# %% [markdown]
# The imported diagram is made of native elements, so it can be edited or exported to any format.

# %%
formulas.save("08_math.svg")
flow.save("08_flowchart.svg")
