"""The corner index: the rank over a small suit, stacked and centred."""

import svgwriter as svg


def corner_index(rank: str, suit: str, ink: svg.Color) -> svg.VStack:
    """Rank and suit in a centred column, in the theme's title and text sizes."""
    return svg.VStack(svg.text(rank, fill=ink).as_role("title"),
                      svg.text(suit, fill=ink).as_role("text"),
                      align="center", gap=2)
