"""``drift``: wander on a closed loop, so the scene repeats without a seam."""

import math

import svgwriter as svg


@svg.preset.behavior
def drift(element: svg.Element, seconds: float, *, rx: float = 60, ry: float = 30, turns: int = 1,
          phase: float = 0, period: float = 4) -> None:
    """Move on a Lissajous loop *rx* by *ry* wide: *turns* times across while once up and down per *period*."""
    angle = math.tau * seconds / period + phase
    element.matrix = element.home.matrix
    element.translate(rx * math.sin(turns * angle), ry * math.sin(angle * 2))
