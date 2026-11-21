"""
Pixel buffers checked and converted for the pure-Python encoders.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .._constants import CHANNEL_MAX, RGBA_CHANNELS

__all__ = ["to_uint8"]


def to_uint8(array: object) -> np.ndarray:
    """Convert floats in ``0..1`` or uint8 to a C-contiguous uint8 array.

    Parameters
    ----------
    array : array-like
        Pixel values; floats are scaled from ``0..1`` and rounded.

    Returns
    -------
    numpy.ndarray
        The ``uint8`` array, unchanged if it already was one.

    Examples
    --------
    >>> to_uint8([0.0, 0.5, 1.0]).tolist()
    [0, 128, 255]
    """
    data = np.asarray(array)
    if data.dtype != np.uint8:
        data = np.clip(np.rint(data * CHANNEL_MAX), 0, CHANNEL_MAX).astype(np.uint8)
    return np.ascontiguousarray(data)


def _check_rgba(rgba: object) -> np.ndarray:
    """Validate and return a uint8 ``(H, W, 4)`` array."""
    data = np.asarray(rgba)
    if data.dtype != np.uint8 or data.ndim != 3 or data.shape[2] != RGBA_CHANNELS:
        raise ValueError(f"expected a uint8 (H, W, 4) array, got {data.dtype} {data.shape}")
    return data


def _composite(rgba: np.ndarray, background: Sequence[int]) -> np.ndarray:
    """Flatten straight RGBA onto an opaque background, returning uint8 ``(H, W, 3)``."""
    alpha = rgba[..., 3:].astype(np.float64) / CHANNEL_MAX
    under = np.asarray(background, np.float64).reshape(1, 1, 3)
    mixed = rgba[..., :3] * alpha + under * (1.0 - alpha)
    return np.clip(np.rint(mixed), 0, CHANNEL_MAX).astype(np.uint8)
