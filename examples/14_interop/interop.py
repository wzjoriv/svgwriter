"""# Interop

You will build: a board mixing a matplotlib chart, a network graph, a dial of your own and pictures from
other libraries.

Run it from this folder with ``python interop.py``, or open ``interop.ipynb``. The matplotlib and networkx
cells are skipped when those packages are not installed.
"""

import importlib.util

import numpy as np

import svgwriter as svg

# %% [markdown]
# A board of three columns by two rows. Each item is placed by its top-left corner.

# %%
CELL_W, CELL_H = 260, 160
doc = svg.Document(3 * CELL_W, 2 * CELL_H)
doc.rect(0, 0, 3 * CELL_W, 2 * CELL_H, fill="#f8fafc")


def cell(column: int, row: int) -> tuple[float, float]:
    """Top-left corner of a board cell, with a margin."""
    return column * CELL_W + 12, row * CELL_H + 12


doc

# %% [markdown]
# A matplotlib figure goes straight into `add`, and becomes shapes and text like the rest of the drawing.

# %%
if importlib.util.find_spec("matplotlib") is not None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(2.5, 1.9))
    x = np.linspace(0, 2 * np.pi, 60)
    ax.plot(x, np.sin(x), color="#7c3aed")
    ax.fill_between(x, np.sin(x), alpha=0.2, color="#7c3aed")
    ax.set_title("matplotlib")
    doc.add(fig).place(*cell(0, 0), at="top_left")
    plt.close(fig)
doc

# %% [markdown]
# A networkx graph is drawn as circles, lines and labels; a node's `fill` attribute colours it.
# python-igraph and rustworkx graphs work the same way.

# %%
if importlib.util.find_spec("networkx") is not None:
    import networkx as nx

    graph = nx.Graph([("a", "b"), ("b", "c"), ("c", "a"), ("c", "d"), ("d", "e")])
    graph.nodes["c"]["fill"] = "#f59e0b"
    doc.add(graph).scale(0.45).place(*cell(1, 0), at="top_left")
doc

# %% [markdown]
# Give your own class a `__svgwriter__` method that returns what to draw, and `add` accepts it.

# %%
class Gauge:
    """A dial reading ``value`` from 0 to 1."""

    def __init__(self, value: float) -> None:
        self.value = value

    def __svgwriter__(self) -> svg.Group:
        dial = svg.Group()
        dial += svg.circle(60, 60, 50, fill="#e2e8f0")
        dial += svg.circle(60, 60, 50, fill="none", stroke="#0ea5e9", stroke_width=10,
                           stroke_dasharray=(314 * self.value, 314), transform="rotate(-90 60 60)")
        dial += svg.text(f"{self.value:.0%}", x=60, y=68, font_size=22, text_anchor="middle", fill="#0f172a",
                         font_family="Arial, Helvetica, sans-serif")
        return dial


doc.add(Gauge(0.72)).place(*cell(2, 0), at="top_left")
doc

# %% [markdown]
# Objects that show themselves in Jupyter with `_repr_svg_` work too, so many plotting libraries just work.

# %%
class Swatch:
    """Anything that renders itself with ``_repr_svg_``."""

    def _repr_svg_(self) -> str:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="110" height="110" viewBox="0 0 110 110">'
            '<rect width="110" height="110" rx="14" fill="#fda4af"/>'
            '<path d="M20 80 L55 20 L90 80 Z" fill="#9f1239"/></svg>'
        )


doc.add(Swatch()).place(*cell(0, 1), at="top_left")
doc

# %% [markdown]
# Objects that show a picture with `_repr_png_` become an image, and so does a plain numpy array.

# %%
class Heat:
    """Raster-only: PNG bytes from ``_repr_png_``."""

    def _repr_png_(self) -> bytes:
        u, v = np.mgrid[0:64, 0:64] / 63
        return svg.Image(np.dstack([u, v, 1 - u * v]), 0, 0, 64, 64).pixels.encode("png")


doc.add(Heat()).scale(1.8).place(*cell(1, 1), at="top_left")
ramp = np.tile(np.linspace(0, 1, 64), (16, 1))
doc.add(ramp).scale(2.5).place(*cell(2, 1), at="top_left")
doc

# %% [markdown]
# Save the board. Next: [15 Animation](../15_animation/animation.py) makes things move.

# %%
doc.save("14_interop.svg")
