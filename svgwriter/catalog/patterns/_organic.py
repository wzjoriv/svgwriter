"""
Curved and scattered patterns: waves, zigzag and seeded noise.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from typing import Any

from ...model.color.color import Color
from ...model.elements import Pattern, Polygon, Rect
from ..preset import pattern
from ._constants import (
    DEFAULT_GAP,
    LINE_WIDTH,
    NOISE_CELL,
    NOISE_DENSITY,
    NOISE_FAINTEST,
    NOISE_TILE,
    ROLE,
    WAVE_AMPLITUDE,
    WAVE_LENGTH,
    WAVE_SAMPLES,
)
from ._tile import ink, tile

__all__ = ["noise", "waves", "zigzag"]


def _band(profile: Callable[[float], float], wavelength: float, samples: int, middle: float,
          width: float) -> Polygon:
    """A closed band *width* thick following ``middle + profile(x)`` across one *wavelength*."""
    xs = [wavelength * i / samples for i in range(samples + 1)]
    top = [(x, middle + profile(x) - width / 2) for x in xs]
    bottom = [(x, middle + profile(x) + width / 2) for x in reversed(xs)]
    return Polygon([*top, *bottom])


@pattern
def waves(*, wavelength: float = WAVE_LENGTH, amplitude: float = WAVE_AMPLITUDE, gap: float = DEFAULT_GAP,
          width: float = 2 * LINE_WIDTH, angle: float = 0.0, color: Color | str | None = None,
          role: str | None = ROLE, background: Color | str | None = None, **kwargs: Any) -> Pattern:
    """Rows of sine waves.

    Parameters
    ----------
    wavelength : float, optional
        Length of one wave. Defaults to 16.
    amplitude : float, optional
        Height of a crest above the row's middle. Defaults to 3.
    gap : float, optional
        Space between rows, beyond the waves' own height. Defaults to 6.
    width : float, optional
        Line thickness. Defaults to 2.
    angle : float, optional
        Rotation in degrees. Defaults to 0.
    color, role, background, **kwargs
        As for :func:`svgwriter.catalog.patterns.stripes`.

    Returns
    -------
    Pattern
        The wave paint.

    See Also
    --------
    zigzag : Straight-sided waves.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.patterns.waves(wavelength=20).get("width")
    20
    """
    height = 2 * amplitude + width + gap
    line = _band(lambda x: amplitude * math.sin(math.tau * x / wavelength), wavelength, WAVE_SAMPLES, height / 2,
                 width)
    return tile(wavelength, height, [ink(line, color, role)], angle=angle, background=background, **kwargs)


@pattern
def zigzag(*, wavelength: float = WAVE_LENGTH / 2, amplitude: float = WAVE_AMPLITUDE, gap: float = DEFAULT_GAP,
           width: float = 2 * LINE_WIDTH, angle: float = 0.0, color: Color | str | None = None,
           role: str | None = ROLE, background: Color | str | None = None, **kwargs: Any) -> Pattern:
    """Rows of chevrons.

    Parameters
    ----------
    wavelength : float, optional
        Length of one zig and zag. Defaults to 8.
    amplitude : float, optional
        Height of a peak above the row's middle. Defaults to 3.
    gap : float, optional
        Space between rows, beyond the zigzag's own height. Defaults to 6.
    width : float, optional
        Line thickness. Defaults to 2.
    angle : float, optional
        Rotation in degrees. Defaults to 0.
    color, role, background, **kwargs
        As for :func:`svgwriter.catalog.patterns.stripes`.

    Returns
    -------
    Pattern
        The zigzag paint.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.patterns.zigzag().children[0].points)
    6
    """
    height = 2 * amplitude + width + gap
    half = wavelength / 2
    line = _band(lambda x: amplitude * (1 - 2 * abs(x - half) / half), wavelength, 2,
                 height / 2, width)
    return tile(wavelength, height, [ink(line, color, role)], angle=angle, background=background, **kwargs)


@pattern
def noise(*, seed: int = 0, density: float = NOISE_DENSITY, cell: float = NOISE_CELL, size: int = NOISE_TILE,
          color: Color | str | None = None, role: str | None = ROLE, background: Color | str | None = None,
          **kwargs: Any) -> Pattern:
    """Grain: a tile of *cell*-sized specks of random opacity, the same for the same *seed*.

    Parameters
    ----------
    seed : int, optional
        Random seed; equal seeds give equal tiles. Defaults to 0.
    density : float, optional
        Share of cells holding a speck, ``0..1``. Defaults to 0.5.
    cell : float, optional
        Side of a speck. Defaults to 2.
    size : int, optional
        Side of the repeating tile, in user units. Defaults to 32.
    color, role, background, **kwargs
        As for :func:`svgwriter.catalog.patterns.stripes`.

    Returns
    -------
    Pattern
        The noise paint.

    See Also
    --------
    svgwriter.catalog.filters.grain : Noise as a filter over any element.

    Examples
    --------
    >>> import svgwriter as svg
    >>> a, b = svg.patterns.noise(seed=3), svg.patterns.noise(seed=3)
    >>> str(a) == str(b), len(a.children) > 0
    (True, True)
    """
    generator = random.Random(seed)
    cells = int(size // cell)
    specks = []
    for row in range(cells):
        for column in range(cells):
            if generator.random() < density:
                speck = ink(Rect(column * cell, row * cell, cell, cell), color, role)
                speck.fill_opacity = round(NOISE_FAINTEST + (1 - NOISE_FAINTEST) * generator.random(), 2)
                specks.append(speck)
    return tile(cells * cell, cells * cell, specks, background=background, **kwargs)
