"""
Line presets: grid, spiral and wave.
"""

from __future__ import annotations

import math
from typing import Any

from ...model.elements.shapes import Path
from ...model.pathdata.builder import PathBuilder
from ..preset import shape
from ._constants import (
    FULL_TURN,
    ROUNDING_EPSILON,
    SINE_CONTROL_X,
    SINE_CONTROL_Y,
    SPIRAL_SEGMENTS_PER_TURN,
    WAVE_CYCLES,
    WAVE_KINDS,
)

__all__ = ["grid", "spiral", "wave"]

Vertex = tuple[float, float]


def _steps(origin: float, extent: float, count: int | None, spacing: float | None) -> list[float]:
    if spacing is None:
        cells = count or 1
        return [origin + extent * index / cells for index in range(cells + 1)]
    total = int(extent / spacing + ROUNDING_EPSILON)
    return [origin + spacing * index for index in range(total + 1)]


@shape(role="grid")
def grid(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    rows: int | None = None,
    cols: int | None = None,
    spacing: float | tuple[float, float] | None = None,
    **kwargs: Any,
) -> Path:
    """Build graph paper: horizontal and vertical lines over a rectangle.

    Give either `rows` and `cols`, which split the rectangle into that many cells, or `spacing`.

    Parameters
    ----------
    x, y : float
        Top-left corner.
    width, height : float
        Size of the grid.
    rows, cols : int, optional
        Number of cell rows and columns; the grid has one more line of each, border included.
    spacing : float or (float, float), optional
        Distance between lines, or ``(horizontal, vertical)`` distances. Lines start at the
        top-left corner and stop at the last one that fits.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Path`;
        ``fill`` defaults to ``"none"``.

    Returns
    -------
    Path
        All lines as one path.

    Raises
    ------
    ValueError
        If neither or both of the cell counts and `spacing` are given, or a count or spacing is not positive.

    See Also
    --------
    svgwriter.catalog.builder.dashed_line : A single dashed line.

    Examples
    --------
    >>> from svgwriter.catalog.builder import grid
    >>> str(grid(0, 0, 20, 10, rows=1, cols=2))
    '<path d="M0 0 L20 0 M0 10 L20 10 M0 0 L0 10 M10 0 L10 10 M20 0 L20 10" fill="none" class="role-grid"/>'
    >>> int(grid(0, 0, 20, 20, spacing=5).bbox.width)
    20
    """
    by_count = rows is not None or cols is not None
    if by_count == (spacing is not None) or (by_count and (rows is None or cols is None)):
        raise ValueError("give rows and cols, or spacing")
    step_x, step_y = spacing if isinstance(spacing, tuple) else (spacing, spacing)
    if any(value is not None and value <= 0 for value in (rows, cols, step_x, step_y)):
        raise ValueError("rows, cols and spacing must be positive")
    ys = _steps(y, height, rows, step_y)
    xs = _steps(x, width, cols, step_x)
    builder = PathBuilder()
    for line in ys:
        builder.move_to(x, line).line_to(x + width, line)
    for line in xs:
        builder.move_to(line, y).line_to(line, y + height)
    kwargs.setdefault("fill", "none")
    return Path(builder, **kwargs)


@shape(role="line")
def spiral(cx: float, cy: float, *, turns: float, start_radius: float, end_radius: float, **kwargs: Any) -> Path:
    """Build an Archimedean spiral from smooth cubic segments.

    The radius changes linearly with the angle. The curve starts to the right of the center and
    winds clockwise.

    Parameters
    ----------
    cx, cy : float
        Center.
    turns : float
        Number of revolutions; fractions are allowed.
    start_radius, end_radius : float
        Distance from the center at the start and at the end.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Path`;
        ``fill`` defaults to ``"none"``.

    Returns
    -------
    Path
        The open spiral.

    Raises
    ------
    ValueError
        If `turns` is not positive.

    See Also
    --------
    wave : A smooth line along a straight axis.

    Examples
    --------
    >>> from svgwriter.catalog.builder import spiral
    >>> round(spiral(0, 0, turns=2, start_radius=0, end_radius=20).bbox.width)
    35
    """
    if turns <= 0:
        raise ValueError(f"turns must be positive, got {turns}")
    count = math.ceil(turns * SPIRAL_SEGMENTS_PER_TURN)
    sweep = math.radians(FULL_TURN) * turns
    pitch = (end_radius - start_radius) / sweep
    step = sweep / count
    reach = 4 / 3 * math.tan(step / 4)

    def at(angle: float) -> tuple[Vertex, Vertex]:
        radius = start_radius + pitch * angle
        cos, sin = math.cos(angle), math.sin(angle)
        return (cx + radius * cos, cy + radius * sin), (pitch * cos - radius * sin, pitch * sin + radius * cos)

    start, slope = at(0.0)
    builder = PathBuilder().move_to(*start)
    for index in range(1, count + 1):
        end, end_slope = at(step * index)
        builder.curve_to(
            start[0] + slope[0] * reach,
            start[1] + slope[1] * reach,
            end[0] - end_slope[0] * reach,
            end[1] - end_slope[1] * reach,
            *end,
        )
        start, slope = end, end_slope
    kwargs.setdefault("fill", "none")
    return Path(builder, **kwargs)


def _sine(builder: PathBuilder, x: float, y: float, width: float, amplitude: float, wavelength: float) -> None:
    half = wavelength / 2
    full, rest = divmod(width, half)
    sign = -1.0
    segments = int(full) + (1 if rest > ROUNDING_EPSILON * width else 0)
    for index in range(segments):
        left = x + index * half
        span = min(half, x + width - left)
        points = [
            (left, y),
            (left + SINE_CONTROL_X * half, y + sign * SINE_CONTROL_Y * amplitude),
            (left + half - SINE_CONTROL_X * half, y + sign * SINE_CONTROL_Y * amplitude),
            (left + half, y),
        ]
        if span < half:
            points = _split(points, span / half)
        builder.curve_to(*points[1], *points[2], *points[3])
        sign = -sign


def _split(points: list[Vertex], fraction: float) -> list[Vertex]:
    low, high = 0.0, 1.0
    for _ in range(60):
        mid = (low + high) / 2
        reached = _bezier_x(points, mid)
        if reached < points[0][0] + (points[3][0] - points[0][0]) * fraction:
            low = mid
        else:
            high = mid
    t = (low + high) / 2
    level = points
    left = [level[0]]
    while len(level) > 1:
        level = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(level, level[1:], strict=False)]
        left.append(level[0])
    return [left[0], left[1], left[2], left[3]]


def _bezier_x(points: list[Vertex], t: float) -> float:
    u = 1 - t
    return u**3 * points[0][0] + 3 * u * u * t * points[1][0] + 3 * u * t * t * points[2][0] + t**3 * points[3][0]


def _polyline(
    builder: PathBuilder, x: float, y: float, width: float, amplitude: float, wavelength: float, kind: str
) -> None:
    cycle = WAVE_KINDS[kind]
    previous: Vertex | None = None
    index = 0
    while True:
        for phase, level in cycle:
            px = x + (index + phase) * wavelength
            if px > x + width + ROUNDING_EPSILON:
                if previous is not None:
                    ratio = (x + width - previous[0]) / (px - previous[0])
                    builder.line_to(x + width, previous[1] + (y - amplitude * level - previous[1]) * ratio)
                return
            point = (px, y - amplitude * level)
            if previous is None:
                builder.move_to(*point)
            else:
                builder.line_to(*point)
            previous = point
            if px >= x + width - ROUNDING_EPSILON:
                return
        index += 1


@shape(role="line")
def wave(
    x: float,
    y: float,
    width: float,
    *,
    amplitude: float,
    wavelength: float,
    kind: str = "sine",
    **kwargs: Any,
) -> Path:
    """Build a periodic line along a horizontal axis.

    The sine wave is made of cubic segments, one per half wavelength; the other kinds are polylines.
    The wave is cut at `width`, so it need not hold a whole number of wavelengths.

    Parameters
    ----------
    x, y : float
        Start of the axis; ``y`` is the centerline.
    width : float
        Length of the wave along the axis.
    amplitude : float
        Distance from the centerline to the crests.
    wavelength : float
        Length of one full cycle.
    kind : {"sine", "square", "triangle", "sawtooth"}, optional
        Shape of the wave. Sine and triangle start on the centerline and rise first; square starts at
        the crest; sawtooth starts at the trough and ramps up. Defaults to ``"sine"``.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Path`;
        ``fill`` defaults to ``"none"``.

    Returns
    -------
    Path
        The open wave.

    Raises
    ------
    ValueError
        If `kind` is unknown or `width` or `wavelength` is not positive.

    See Also
    --------
    spiral : A smooth curve around a center.

    Examples
    --------
    >>> from svgwriter.catalog.builder import wave
    >>> box = wave(0, 20, 100, amplitude=10, wavelength=50).bbox
    >>> round(box.height, 1)
    20.0
    >>> len(wave(0, 0, 40, amplitude=5, wavelength=20, kind="square").d)
    8
    """
    if kind not in WAVE_CYCLES:
        raise ValueError(f"unknown wave kind {kind!r}; choose from {', '.join(WAVE_CYCLES)}")
    if width <= 0 or wavelength <= 0:
        raise ValueError("width and wavelength must be positive")
    builder = PathBuilder().move_to(x, y) if kind == "sine" else PathBuilder()
    if kind == "sine":
        _sine(builder, x, y, width, amplitude, wavelength)
    else:
        _polyline(builder, x, y, width, amplitude, wavelength, kind)
    kwargs.setdefault("fill", "none")
    return Path(builder, **kwargs)
