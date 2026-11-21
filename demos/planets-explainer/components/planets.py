"""The planets, read from ``assets/data/planets.csv``."""

import csv
from pathlib import Path
from typing import NamedTuple

DATA = Path("assets/data/planets.csv")


class Planet(NamedTuple):
    """A planet: its name, mean distance from the Sun in AU, colour and drawn radius (not to scale)."""

    name: str
    au: float
    color: str
    radius: float


def read_planets(path: Path = DATA) -> list[Planet]:
    """Every planet in the table, nearest first."""
    with path.open(encoding="utf-8") as file:
        return [Planet(row["name"], float(row["au"]), row["color"], float(row["radius"]))
                for row in csv.DictReader(file)]
