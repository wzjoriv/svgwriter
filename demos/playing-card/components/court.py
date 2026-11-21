"""The face of a court card: a framed panel with a large letter between two suits."""

import svgwriter as svg


def court(rank: str, suit: str, ink: svg.Color, accent: svg.Color, *, width: float, height: float,
          radius: float) -> svg.VStack:
    """A *width* x *height* panel framed in *accent*, holding the rank letter between two suit symbols."""
    frame = svg.rect(rx=radius, fill=accent.with_alpha(0.12), stroke=accent, stroke_width=1.5)
    return svg.VStack(svg.text(suit, font_size=height * 0.16, fill=ink),
                      svg.text(rank, font_size=height * 0.42, font_weight="bold", fill=ink),
                      svg.text(suit, font_size=height * 0.16, fill=ink, transform="rotate(180)"),
                      width=width, height=height, align="center", justify="space_around", background=frame)
