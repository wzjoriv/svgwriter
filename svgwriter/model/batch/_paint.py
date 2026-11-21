"""
Colour columns: colour lists and RGB(A) arrays as hex text per item, and the built-in colormaps.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import cache
from numbers import Real
from typing import Any

import numpy as np

from ..color.color import Color, as_color
from ._constants import CHANNEL_MAX, COLORMAPS, RGB, RGBA

__all__ = ["colormap", "colormaps", "hex_column", "is_color_column", "rgba_of"]


def colormaps() -> list[str]:
    """Names of the built-in colormaps.

    Returns
    -------
    list of str
        The names :func:`colormap` accepts, sorted.

    Examples
    --------
    >>> import svgwriter as svg
    >>> "viridis" in svg.batch.colormaps()
    True
    """
    return sorted(COLORMAPS)


@cache
def _stops(name: str) -> np.ndarray:
    if name not in COLORMAPS:
        raise ValueError(f"unknown colormap {name!r}; choose one of {', '.join(colormaps())}")
    return np.array([as_color(stop).rgba[:RGB] for stop in COLORMAPS[name]])


def colormap(name: str, values: Any, *, vmin: float | None = None, vmax: float | None = None) -> np.ndarray:
    """Colours for *values* from a perceptual colormap, as an ``(..., 3)`` RGB array in ``0..1``.

    Pass the result as ``fill`` or ``stroke`` of a batch; each item gets its own colour.

    Parameters
    ----------
    name : str
        A colormap: ``"viridis"``, ``"plasma"``, ``"inferno"``, ``"magma"``, ``"cividis"``,
        ``"turbo"`` or ``"grays"``.
    values : array_like
        The data to colour, any shape.
    vmin, vmax : float, optional
        Values mapped to the ends of the map; values outside are clipped. Default to the smallest
        and largest of *values*.

    Returns
    -------
    numpy.ndarray
        ``values.shape + (3,)`` RGB in ``0..1``.

    Raises
    ------
    ValueError
        If *name* is not a built-in colormap.

    See Also
    --------
    colormaps : The available names.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.batch.colormap("viridis", [0, 1]).round(3).tolist()
    [[0.267, 0.004, 0.329], [0.992, 0.906, 0.145]]
    >>> dots = svg.batch.circles([0, 10, 20], 0, 2, fill=svg.batch.colormap("grays", [0, 5, 10]))
    >>> dots.column("fill").tolist()
    ['#000000', '#808080', '#ffffff']
    """
    stops = _stops(name)
    data = np.asarray(values, dtype=float)
    low = float(np.min(data)) if vmin is None else float(vmin)
    high = float(np.max(data)) if vmax is None else float(vmax)
    span = high - low
    unit = np.clip((data - low) / span, 0.0, 1.0) if span else np.zeros_like(data)
    positions = np.linspace(0.0, 1.0, len(stops))
    return np.stack([np.interp(unit, positions, stops[:, channel]) for channel in range(RGB)], axis=-1)


def _is_numeric_color(value: Any) -> bool:
    return isinstance(value, (tuple, list)) and len(value) in (RGB, RGBA) and all(
        isinstance(part, Real) for part in value)


def is_color_column(value: Any) -> bool:
    """Whether *value* gives one colour per item (a list of colours or an ``(..., 3|4)`` array)."""
    if isinstance(value, np.ndarray):
        if value.dtype.kind in "fiu":
            return value.ndim >= 2 and value.shape[-1] in (RGB, RGBA)
        return value.ndim >= 1
    return isinstance(value, (list, tuple)) and not _is_numeric_color(value)


def _unit_rgba(array: np.ndarray) -> np.ndarray:
    scaled = array / CHANNEL_MAX if array.dtype.kind in "iu" else array.astype(float)
    return np.clip(scaled, 0.0, 1.0)


def rgba_of(value: Any) -> np.ndarray:
    """A colour column as an ``(..., 4)`` RGBA array in ``0..1``."""
    if isinstance(value, np.ndarray) and value.dtype.kind in "fiu":
        unit = _unit_rgba(value)
        if unit.shape[-1] == RGB:
            unit = np.concatenate([unit, np.ones(unit.shape[:-1] + (1,))], axis=-1)
        return unit
    items = np.asarray(value, dtype=object)
    flat = items.reshape(-1)
    known: dict[Any, tuple[float, ...]] = {}
    rows = [known[v] if v in known else known.setdefault(v, as_color(v).rgba) for v in flat.tolist()]
    return np.array(rows, dtype=float).reshape(items.shape + (RGBA,))


def _hex(rgb: np.ndarray) -> np.ndarray:
    codes = np.rint(rgb * CHANNEL_MAX).astype(np.int64)
    packed = (codes[..., 0] << 16) | (codes[..., 1] << 8) | codes[..., 2]
    unique, inverse = np.unique(packed, return_inverse=True)
    texts = np.array([f"#{code:06x}" for code in unique.tolist()], dtype=object)
    return texts[inverse].reshape(packed.shape)


def hex_column(value: Sequence[Any] | np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    """Hex text per item and, when any colour is translucent, its alpha per item.

    Parameters
    ----------
    value : sequence or numpy.ndarray
        Colours (names, hex text or :class:`Color`) or an ``(..., 3|4)`` array, ``0..1`` floats or
        ``0..255`` integers.

    Returns
    -------
    (numpy.ndarray, numpy.ndarray or None)
        The item-shaped hex texts and alphas.
    """
    if isinstance(value, np.ndarray) and value.dtype.kind in "fiu":
        rgba = rgba_of(value)
        alpha = rgba[..., RGB] if value.shape[-1] == RGBA else None
        return _hex(rgba[..., :RGB]), alpha
    items = np.asarray(value, dtype=object)
    flat = items.reshape(-1)
    known: dict[Any, tuple[str, float]] = {}
    for item in set(flat.tolist()):
        color = item if isinstance(item, Color) else as_color(item)
        known[item] = (color.hex[: 1 + 2 * RGB], color.rgba[RGB])
    texts = np.array([known[v][0] for v in flat.tolist()], dtype=object).reshape(items.shape)
    alphas = np.array([known[v][1] for v in flat.tolist()]).reshape(items.shape)
    return texts, alphas if bool(np.any(alphas < 1.0)) else None
