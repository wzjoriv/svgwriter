"""
``PresentationKeywords``: the presentation attributes ``PresentationAttributes`` takes through ``**kwargs``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from ..._internal._typing import FillRule, Opacity
    from ...attributes.length import LengthLike
    from ...color.color import Color
    from ...ops.typeface import Typeface
    from ..core import Element
    from ..text import TextDecoration

__all__ = ["PresentationKeywords"]


class PresentationKeywords(TypedDict, total=False):
    """Typed keywords for the presentation attributes without a named parameter in `PresentationAttributes`.

    Together with the parameters of :class:`PresentationAttributes` they cover
    every SVG 1.1 presentation attribute. The generated element signatures
    list them as keyword-only parameters; the values reach the element
    through ``**kwargs`` like any other attribute.

    See Also
    --------
    PresentationAttributes : The attribute group with the common properties as named parameters.

    Examples
    --------
    >>> from svgwriter.elements._behavior._presentation import PresentationKeywords
    >>> "letter_spacing" in PresentationKeywords.__annotations__
    True
    """

    alignment_baseline: str | None
    baseline_shift: LengthLike | str | None
    clip: str | None
    clip_rule: FillRule | None
    color_interpolation: str | None
    color_interpolation_filters: str | None
    color_profile: str | None
    color_rendering: str | None
    direction: str | None
    dominant_baseline: str | None
    enable_background: str | None
    flood_color: Color | str | None
    flood_opacity: Opacity | None
    font: Typeface | str | None
    font_size_adjust: float | str | None
    font_stretch: str | None
    font_style: str | None
    font_variant: str | None
    glyph_orientation_horizontal: float | str | None
    glyph_orientation_vertical: float | str | None
    image_rendering: str | None
    kerning: LengthLike | str | None
    letter_spacing: LengthLike | str | None
    lighting_color: Color | str | None
    marker: str | Element | None
    marker_end: str | Element | None
    marker_mid: str | Element | None
    marker_start: str | Element | None
    overflow: str | None
    pointer_events: str | None
    shape_rendering: str | None
    stop_color: Color | str | None
    stop_opacity: Opacity | None
    text_decoration: TextDecoration | str | None
    text_rendering: str | None
    unicode_bidi: str | None
    word_spacing: LengthLike | str | None
    writing_mode: str | None
