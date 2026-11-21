"""
CSS Color 4 functional notations behind ``parse_color``: channels, angles, ``none`` and ``/ alpha``.
"""

from __future__ import annotations

import colorsys
from collections.abc import Callable
from typing import TYPE_CHECKING

from ._constants import ANGLE_UNITS, CHANNEL_MAX, COLOR_SPACES, DEGREES, PERCENT_MAX, PERCENT_REFERENCE
from ._spaces import (
    RGB_SPACES,
    Triple,
    cmyk_to_srgb,
    hsv_to_srgb,
    hwb_to_srgb,
    lab_to_srgb,
    lch_to_lab,
    oklab_to_srgb,
)

if TYPE_CHECKING:
    from .color import Color

__all__ = ["color_function"]

NONE = "none"
LEGACY_UNIFORM = frozenset({"rgb", "rgba"})
"""Functions whose comma syntax needs all-number or all-percent channels."""


def _number(token: str, percent: float, text: str) -> float:
    """A channel: ``none`` is 0, ``n%`` is that share of *percent*, a plain number is itself."""
    try:
        if token == NONE:
            return 0.0
        if token.endswith("%"):
            return float(token[:-1]) / PERCENT_MAX * percent
        return float(token)
    except ValueError:
        raise ValueError(f"invalid channel {token!r} in {text!r}") from None


def _hue(token: str, text: str) -> float:
    for unit, factor in ANGLE_UNITS.items():
        if token.endswith(unit):
            return _number(token[: -len(unit)], 1.0, text) * factor
    return _number(token, 1.0, text)


def _alpha(token: str | None, text: str) -> float:
    return 1.0 if token is None else min(max(_number(token, 1.0, text), 0.0), 1.0)


def _split(body: str, text: str, size: int) -> tuple[list[str], str | None]:
    """Channel tokens and the alpha token, from modern ``a b c / d`` or legacy ``a, b, c, d`` syntax."""
    main, slash, alpha = body.partition("/")
    tokens = main.replace(",", " ").split()
    if slash:
        if len(tokens) != size or not alpha.strip():
            raise ValueError(f"expected {size} channels before '/': {text!r}")
        return tokens, alpha.strip()
    if len(tokens) not in (size, size + 1):
        raise ValueError(f"expected {size} channels and an optional alpha: {text!r}")
    return tokens[:size], tokens[size] if len(tokens) > size else None


def _rgb(t: list[str], text: str) -> Triple:
    r, g, b = (_number(c, CHANNEL_MAX, text) / CHANNEL_MAX for c in t)
    return (r, g, b)


def _cylinder(convert: Callable[[float, float, float], Triple]) -> Callable[[list[str], str], Triple]:
    return lambda t, text: convert(_hue(t[0], text), _number(t[1], PERCENT_MAX, text) / PERCENT_MAX,
                                   _number(t[2], PERCENT_MAX, text) / PERCENT_MAX)


def _hsl(hue: float, saturation: float, lightness: float) -> Triple:
    return colorsys.hls_to_rgb((hue % DEGREES) / DEGREES, min(max(lightness, 0.0), 1.0), min(max(saturation, 0.0), 1.0))


def _lab_like(kind: str, polar: bool, convert: Callable[[Triple], Triple]) -> Callable[[list[str], str], Triple]:
    scale = PERCENT_REFERENCE[kind]

    def build(t: list[str], text: str) -> Triple:
        lightness, second = _number(t[0], scale[0], text), _number(t[1], scale[1], text)
        third = _hue(t[2], text) if polar else _number(t[2], scale[2], text)
        values = (lightness, second, third)
        return convert(lch_to_lab(values) if polar else values)

    return build


FUNCTIONS: dict[str, tuple[int, Callable[[list[str], str], Triple]]] = {
    "rgb": (3, _rgb), "rgba": (3, _rgb),
    "hsl": (3, _cylinder(_hsl)), "hsla": (3, _cylinder(_hsl)),
    "hsv": (3, _cylinder(hsv_to_srgb)), "hsva": (3, _cylinder(hsv_to_srgb)),
    "hwb": (3, _cylinder(hwb_to_srgb)),
    "lab": (3, _lab_like("lab", False, lab_to_srgb)), "lch": (3, _lab_like("lch", True, lab_to_srgb)),
    "oklab": (3, _lab_like("oklab", False, oklab_to_srgb)), "oklch": (3, _lab_like("oklch", True, oklab_to_srgb)),
    "device-cmyk": (4, lambda t, text: cmyk_to_srgb(*(_number(c, 1.0, text) for c in t))),
}


def color_function(kind: str, body: str, text: str) -> Color:
    """Build a color from the body of a CSS color function, clipped to the sRGB gamut.

    Parameters
    ----------
    kind : str
        The function name: ``rgb``, ``rgba``, ``hsl``, ``hsla``, ``hsv``, ``hsva``, ``hwb``, ``lab``,
        ``lch``, ``oklab``, ``oklch``, ``color`` or ``device-cmyk``.
    body : str
        The text between the parentheses, lower-cased.
    text : str
        The whole color text, for error messages.

    Returns
    -------
    Color
        The color in sRGB; channels outside the gamut are clipped to ``0..1``.

    Raises
    ------
    ValueError
        For a wrong number of channels, an unknown ``color()`` space or a malformed number.
    """
    from .color import Color

    if kind == "color":
        space, _, rest = body.strip().partition(" ")
        if space not in COLOR_SPACES:
            raise ValueError(f"unknown color space {space!r} in {text!r}; expected one of {sorted(COLOR_SPACES)}")
        tokens, alpha = _split(rest, text, 3)
        rgb = RGB_SPACES[space]([_number(c, 1.0, text) for c in tokens])
    else:
        size, convert = FUNCTIONS[kind]
        tokens, alpha = _split(body, text, size)
        if kind in LEGACY_UNIFORM and "," in body and len({t.endswith("%") for t in tokens}) != 1:
            raise ValueError(f"mixed number and percent channels: {text!r}")
        rgb = convert(tokens, text)
    r, g, b = (min(max(c, 0.0), 1.0) for c in rgb)
    return Color(r, g, b, _alpha(alpha, text))
