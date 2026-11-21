"""The keypad layouts: rows of labels, with ``None`` where the key on the left spans two columns."""

from collections.abc import Callable

import svgwriter as svg

LAYOUTS = {
    "standard 4x5": [
        ["C", "±", "%", "÷"],
        ["7", "8", "9", "×"],
        ["4", "5", "6", "−"],
        ["1", "2", "3", "+"],
        ["0", None, ".", "="],
    ],
    "scientific 5x6": [
        ["sin", "cos", "tan", "log", "ln"],
        ["x²", "√", "(", ")", "÷"],
        ["C", "7", "8", "9", "×"],
        ["±", "4", "5", "6", "−"],
        ["%", "1", "2", "3", "+"],
        ["π", "0", None, ".", "="],
    ],
    "compact 4x4": [
        ["7", "8", "9", "÷"],
        ["4", "5", "6", "×"],
        ["1", "2", "3", "−"],
        ["0", ".", "=", "+"],
    ],
}


def keypad(layout: str, make_key: Callable[[str], svg.Element], *, gap: float, align: str) -> svg.Grid:
    """A grid of ``make_key(label)`` for every label of *layout*; ``None`` widens the key before it."""
    rows = LAYOUTS[layout]
    grid = svg.Grid(columns=len(rows[0]), gap=gap, align=align, justify=align)
    for row in rows:
        for label in row:
            if label is None:
                grid.span(grid.children[-1], columns=2)
            else:
                grid.append(make_key(label))
    return grid
