"""The tide table: a grid of stations and their times, read from ``assets/data/tides.csv``."""

import csv
from pathlib import Path

import svgwriter as svg

DATA = Path("assets/data/tides.csv")
HEADERS = {"station": "Station", "high": "High water", "low": "Low water", "range": "Range"}


def tide_table(width: float, *, family: svg.Typeface, gap: float) -> svg.Grid:
    """A header row and one row per station, *width* mm wide, the first column twice as wide."""
    with DATA.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    cells = [svg.text(label, font_family=family, font_weight="bold").as_role("caption") for label in HEADERS.values()]
    for row in rows:
        cells += [svg.text(row[key], font_family=family).as_role("text") for key in HEADERS]
    return svg.Grid(*cells, columns=["2fr", "1fr", "1fr", "1fr"], gap=(gap, 0), width=width, align="start")
