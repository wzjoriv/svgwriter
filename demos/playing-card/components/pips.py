"""The pips of a number card: columns of suit symbols spread over the card's middle."""

import svgwriter as svg

PIP_COLUMNS = {
    "2": (0, 2, 0), "3": (0, 3, 0), "4": (2, 0, 2), "5": (2, 1, 2), "6": (3, 0, 3),
    "7": (3, 1, 3), "8": (3, 2, 3), "9": (4, 1, 4), "10": (4, 2, 4),
}
"""How many pips each of the three columns holds, by rank."""


def pips(rank: str, suit: str, ink: svg.Color, *, width: float, height: float, size: float) -> svg.HStack:
    """The pips of *rank* in a *width* x *height* box: three columns, each spread from top to bottom.

    An outer column spreads its pips from top to bottom; the middle column keeps a gap at both ends, and a
    single pip sits in the middle.
    The ace has one large pip instead.
    """
    if rank == "A":
        ace = svg.text(suit, font_size=size * 2.6, fill=ink)
        return svg.HStack(ace, width=width, height=height, align="center", justify="center")
    columns = []
    for column, count in enumerate(PIP_COLUMNS[rank]):
        spread = "space_evenly" if column == 1 else "space_between"
        symbols = [svg.text(suit, font_size=size, fill=ink) for _ in range(count)]
        columns.append(svg.VStack(*symbols, height=height, align="center",
                                  justify=spread if count > 1 else "center"))
    return svg.HStack(*columns, width=width, height=height, justify="space_between")
