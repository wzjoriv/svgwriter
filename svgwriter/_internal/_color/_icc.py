"""
ICC colour management through the ``lcms2`` package: profiles, colours and pixels to sRGB.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np

from ._icc_constants import DEFAULT_INTENT, INTENTS, PROFILE_CACHE, SPACE_SCALES

__all__ = ["color_to_srgb", "load_profile", "pixels_to_srgb"]

@lru_cache(maxsize=PROFILE_CACHE)
def load_profile(data: bytes) -> Any:
    """Parse ICC profile bytes once; the same object (and its cached transforms) is reused.

    Parameters
    ----------
    data : bytes
        The ICC profile contents.

    Returns
    -------
    lcms2.Profile or None
        The profile, or None when the data is not a valid profile.

    Examples
    --------
    >>> from svgwriter._internal._color._icc import load_profile
    >>> load_profile(b"not a profile") is None
    True
    """
    from lcms2 import Profile

    try:
        return Profile.from_bytes(data)
    except Exception:
        return None


def _intent(name: str | None) -> str:
    return INTENTS.get(str(name or "").strip().lower(), DEFAULT_INTENT)


def color_to_srgb(profile: Any, components: list[float], intent: str | None = None) -> tuple[float, float, float] | None:
    """Convert one colour given in *profile*'s space to sRGB.

    Parameters
    ----------
    profile : lcms2.Profile
        The source profile.
    components : list of float
        The colour components, ``0..1`` per channel (Lab and XYZ in their natural units).
    intent : str, optional
        SVG rendering intent such as ``"relative-colorimetric"``. Defaults to perceptual.

    Returns
    -------
    tuple of float or None
        sRGB in ``0..1``, or None when the component count does not match the profile.

    Examples
    --------
    >>> from lcms2 import Profile
    >>> from svgwriter._internal._color._icc import color_to_srgb
    >>> print([round(c, 2) for c in color_to_srgb(Profile.srgb(), [1, 0, 0])])
    [1.0, 0.0, 0.0]
    """
    if len(components) != profile.channels:
        return None
    scale = SPACE_SCALES.get(profile.color_space, 1.0)
    values = np.asarray(components, dtype=np.float64) * scale
    try:
        out = profile.transform(values, "sRGB", intent=_intent(intent), out_dtype=np.float64)
    except Exception:
        return None
    r, g, b = (min(max(float(c), 0.0), 1.0) for c in np.ravel(out)[:3])
    return r, g, b


def pixels_to_srgb(profile: Any, rgba: np.ndarray, intent: str | None = None) -> np.ndarray | None:
    """Convert decoded ``uint8`` RGBA pixels from *profile* to sRGB, keeping alpha.

    Parameters
    ----------
    profile : lcms2.Profile
        The pixels' profile (RGB or gray; gray reads the first channel).
    rgba : numpy.ndarray
        ``uint8`` ``(H, W, 4)`` device values.
    intent : str, optional
        SVG rendering intent. Defaults to perceptual.

    Returns
    -------
    numpy.ndarray or None
        ``uint8`` ``(H, W, 4)`` sRGB, or None when the profile cannot describe these pixels.

    Examples
    --------
    >>> import numpy as np
    >>> from lcms2 import Profile
    >>> from svgwriter._internal._color._icc import pixels_to_srgb
    >>> print(pixels_to_srgb(Profile.srgb(), np.full((1, 1, 4), 200, np.uint8)).tolist())
    [[[200, 200, 200, 200]]]
    """
    try:
        if profile.color_space == "RGB":
            return np.asarray(profile.transform(np.ascontiguousarray(rgba), "sRGB", intent=_intent(intent)))
        if profile.color_space == "GRAY":
            rgb = profile.transform(np.ascontiguousarray(rgba[..., :1]), "sRGB", intent=_intent(intent))
            return np.concatenate([np.asarray(rgb, np.uint8).reshape(rgba.shape[:2] + (3,)), rgba[..., 3:]], axis=2)
    except Exception:
        return None
    return None
