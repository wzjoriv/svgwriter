"""
Output colour profiles for exports: resolving ``icc=`` options and converting rendered sRGB pixels.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal, TypeAlias

import numpy as np

from ._icc_constants import DEFAULT_INTENT, ICC_EXTRA_HINT, OUTPUT_PROFILES, PROFILE_CACHE

__all__ = ["IccLike", "OutputProfile", "output_profile", "to_profile"]

IccLike: TypeAlias = "Literal['srgb', 'display-p3'] | bytes"
"""An output profile: ``"srgb"``, ``"display-p3"`` or the bytes of an ICC profile."""


@dataclass(frozen=True)
class OutputProfile:
    """A resolved output profile.

    Parameters
    ----------
    profile : lcms2.Profile
        The parsed profile.
    data : bytes
        The profile bytes to embed.
    space : str
        Its data colour space: ``"RGB"``, ``"CMYK"`` or ``"GRAY"``.
    srgb : bool
        Whether it is the sRGB keyword, so rendered pixels need no conversion.
    name : str
        Its description, used as the PDF output condition.
    """

    profile: Any
    data: bytes
    space: str
    srgb: bool
    name: str


@lru_cache(maxsize=PROFILE_CACHE)
def output_profile(icc: str | bytes) -> OutputProfile:
    """Resolve an ``icc=`` export option once; the result and its transforms are reused.

    Parameters
    ----------
    icc : {"srgb", "display-p3"} or bytes
        A built-in profile keyword or the contents of an ICC profile.

    Returns
    -------
    OutputProfile
        The parsed profile with the bytes to embed.

    Raises
    ------
    ImportError
        If the optional ``color`` extra (``lcms2``) is not installed.
    ValueError
        For an unknown keyword or bytes that are not an ICC profile.

    Examples
    --------
    >>> from svgwriter._internal._icc import lcms_available
    >>> from svgwriter._internal._icc_output import output_profile
    >>> output_profile("display-p3").space if lcms_available() else "RGB"
    'RGB'
    """
    try:
        from lcms2 import Profile
    except ImportError:
        raise ImportError(ICC_EXTRA_HINT) from None
    key = icc.strip().lower() if isinstance(icc, str) else None
    if key is not None:
        if key not in OUTPUT_PROFILES:
            raise ValueError(f"unknown ICC profile {icc!r}; expected one of {sorted(OUTPUT_PROFILES)} or profile bytes")
        profile = Profile.srgb() if key == "srgb" else Profile.builtin(OUTPUT_PROFILES[key])
        data = profile.to_bytes()
    else:
        data = bytes(icc)
        try:
            profile = Profile.from_bytes(data)
        except Exception as error:
            raise ValueError(f"the icc bytes are not a readable ICC profile: {error}") from None
    space = str(getattr(profile.color_space, "value", profile.color_space)).upper()
    return OutputProfile(profile, data, space, key == "srgb", str(profile.description or space))


def to_profile(rgba: np.ndarray, target: OutputProfile) -> np.ndarray:
    """Convert rendered ``uint8`` sRGB pixels to the target profile in one LittleCMS pass.

    Parameters
    ----------
    rgba : numpy.ndarray
        Straight ``uint8`` ``(H, W, 4)`` sRGB pixels.
    target : OutputProfile
        An RGB or CMYK profile.

    Returns
    -------
    numpy.ndarray
        ``uint8`` ``(H, W, 4)``: RGBA with alpha kept for an RGB profile (unchanged for sRGB), or
        CMYK ink (255 is full ink) for a CMYK profile.

    Raises
    ------
    ValueError
        If the profile is neither RGB nor CMYK.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter._internal._icc import lcms_available
    >>> from svgwriter._internal._icc_output import output_profile, to_profile
    >>> red = np.array([[[255, 0, 0, 255]]], np.uint8)
    >>> to_profile(red, output_profile("display-p3")).tolist() if lcms_available() else [[[234, 51, 35, 255]]]
    [[[234, 51, 35, 255]]]
    """
    if target.srgb:
        return rgba
    if target.space not in ("RGB", "CMYK"):
        raise ValueError(f"cannot write pixels in a {target.space} profile; use an RGB or CMYK profile")
    source = output_profile("srgb").profile
    converted = np.asarray(source.transform(np.ascontiguousarray(rgba[..., :3]), target.profile,
                                            intent=DEFAULT_INTENT), dtype=np.uint8)
    if target.space == "CMYK":
        return converted
    return np.concatenate([converted, rgba[..., 3:]], axis=2)
