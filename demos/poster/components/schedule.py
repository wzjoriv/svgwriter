"""The morning's plan: a grid of times and activities, read from ``assets/data/schedule.csv``."""

import csv
from pathlib import Path

import svgwriter as svg

DATA = Path("assets/data/schedule.csv")


def schedule(width: float, *, family: svg.Typeface, gap: float) -> svg.Grid:
    """One row per step, *width* mm wide: the time in bold, then what happens."""
    with DATA.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    cells = []
    for row in rows:
        cells += [svg.text(row["time"], font_family=family, font_weight="bold").as_role("text"),
                  svg.text(row["activity"], font_family=family).as_role("text")]
    return svg.Grid(*cells, columns=["1fr", "4fr"], gap=(gap, 0), width=width, align="start")
