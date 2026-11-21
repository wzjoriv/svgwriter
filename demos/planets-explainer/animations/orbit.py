"""``orbit``: circle a centre, faster when closer, as Kepler's third law says."""

import svgwriter as svg

EARTH_TURN = 60.0   # degrees per second for a planet at 1 AU


@svg.preset.behavior
def orbit(element: svg.Element, seconds: float, *, cx: float = 0, cy: float = 0, au: float = 1,
          speed: float = 1.0) -> None:
    """Turn about (cx, cy); the period grows with the distance *au* to the power 3/2, and *speed* scales time."""
    element.t = element.home.t
    element.rotate(-EARTH_TURN * speed * seconds / au ** 1.5, about=(cx, cy))
