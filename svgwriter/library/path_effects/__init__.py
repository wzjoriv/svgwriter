"""
Ready-made path effects: ``el.path_effect("roughen")``, ``"dashed"``, ``"stamp"`` and ``"taper"``; add your own with
``@svg.preset.path_effect``.

Each turns an outline into new path data, so every format draws the result as it looks here.
"""

from __future__ import annotations

from typing import Any

from ..._internal._presets import PATH_EFFECTS
from ...model.pathdata.data import PathData
from ...ops import path_effects as _ops

__all__ = ["dashed", "roughen", "stamp", "taper"]


@PATH_EFFECTS
def roughen(data: PathData, *, segment: float = 4.0, deviation: float = 1.5, seed: int = 0) -> PathData:
    """A hand-drawn wobble: the outline broken into *segment*-long pieces whose ends move up to *deviation*.

    Parameters
    ----------
    data : PathData
        The outline.
    segment : float, optional
        Length of the pieces. Defaults to 4.
    deviation : float, optional
        Largest wobble. Defaults to 1.5.
    seed : int, optional
        Random seed. Defaults to 0.

    Returns
    -------
    PathData
        The roughened outline.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.rect(0, 0, 40, 20, fill="gold").path_effect("roughen", seed=2).tag
    'path'
    """
    return _ops.roughen(data, segment, deviation, seed)


@PATH_EFFECTS
def dashed(data: PathData, *, intervals: tuple[float, ...] = (6.0, 4.0), offset: float = 0.0) -> PathData:
    """Dashes as open paths, ready to stroke.

    Parameters
    ----------
    data : PathData
        The outline.
    intervals : tuple of float, optional
        Dash and gap lengths, alternating. Defaults to ``(6, 4)``.
    offset : float, optional
        Distance into the pattern where the outline starts. Defaults to 0.

    Returns
    -------
    PathData
        The dashes.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.line(0, 0, 40, 0, stroke="black").path_effect("dashed", intervals=(8, 4)).tag
    'path'
    """
    return _ops.dashed(data, intervals, offset)


@PATH_EFFECTS(fills=True)
def stamp(data: PathData, *, shape: Any, spacing: float = 10.0, offset: float = 0.0,
          orient: _ops.StampOrient = "rotate") -> PathData:
    """Copies of *shape* every *spacing* along the outline, as one shape to fill.

    Parameters
    ----------
    data : PathData
        The path to follow.
    shape : Element or PathData
        What to stamp, drawn around its own origin.
    spacing : float, optional
        Distance between copies. Defaults to 10.
    offset : float, optional
        Distance of the first copy. Defaults to 0.
    orient : {"rotate", "translate", "morph"}, optional
        How each copy follows the path. Defaults to "rotate".

    Returns
    -------
    PathData
        The copies.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.line(0, 0, 60, 0, stroke="teal").path_effect("stamp", shape=svg.circle(0, 0, 2)).get("fill")
    'teal'
    """
    return _ops.stamp(data, shape, spacing, offset=offset, orient=orient)


@PATH_EFFECTS(fills=True)
def taper(data: PathData, *, widths: _ops.Widths = (1.0, 6.0, 1.0), samples: int = 64) -> PathData:
    """A stroke whose width changes along the line, as an outline to fill (brush strokes, thinning arrows).

    Parameters
    ----------
    data : PathData
        The centre line.
    widths : float, sequence of float or callable, optional
        The width: one number, values spread evenly along the line, or a function of the position ``0..1``.
        Defaults to ``(1, 6, 1)``, thin at both ends and full in the middle.
    samples : int, optional
        Points taken along each part of the line. Defaults to 64.

    Returns
    -------
    PathData
        The outline.

    Examples
    --------
    >>> import svgwriter as svg
    >>> brush = svg.path("M0 20 C40 0 80 40 120 20", stroke="navy").path_effect("taper", widths=(0, 8, 0))
    >>> str(brush.get("fill")), str(brush.get("stroke"))
    ('navy', 'none')
    """
    return _ops.taper(data, widths, samples=samples)
