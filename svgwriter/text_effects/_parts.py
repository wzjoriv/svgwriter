"""
Shared parts of text effects: sizing to the glyphs, the filter region, SMIL loops and tinted copies.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from ..model.color.color import Color
from ..model.elements import Animate, CompositeOperator, FeComposite, FeFlood, Filter, StandardInput, Text
from ..model.elements.core import Element
from ._constants import REFERENCE_HEIGHT, REGION_EXTENT, REGION_MARGIN, REGION_PAD

__all__ = ["Fit", "fit", "loop", "tinted"]

INDEFINITE = "indefinite"
DISCRETE = "discrete"


@dataclass(frozen=True)
class Fit:
    """How an effect sizes itself to a text: a *scale* for lengths and the filter *area* around the glyphs."""

    scale: float
    area: dict[str, Any]

    def __call__(self, length: float) -> float:
        """*length*, tuned for reference glyphs, scaled to these glyphs."""
        return round(length * self.scale, 3)

    def frequency(self, pair: Sequence[float]) -> tuple[float, float]:
        """A noise frequency pair scaled so the noise keeps its size relative to the glyphs."""
        return (round(pair[0] / self.scale, 4), round(pair[1] / self.scale, 4))

    def values(self, items: Iterable[float | Sequence[float]], *, frequency: bool = False) -> list[str]:
        """Animation values scaled like lengths, or like frequencies for pairs."""
        texts = []
        for item in items:
            if isinstance(item, Sequence):
                texts.append(" ".join(f"{v:g}" for v in self.frequency(item)))
            else:
                texts.append(f"{item if frequency else self(item):g}")
        return texts

    def filter(self, *primitives: Element) -> Filter:
        """A filter of *primitives* over the glyphs and room around them, computed in sRGB."""
        return Filter(*primitives, color_interpolation_filters="sRGB", **self.area)


def fit(text: Text) -> Fit:
    """The sizing of an effect on *text*: its visible glyphs (only the range, on an isolated layer)."""
    box = text.visible_bbox()
    if box is None or box.height <= 0:
        return Fit(1.0, {"x": REGION_MARGIN, "y": REGION_MARGIN, "width": REGION_EXTENT, "height": REGION_EXTENT})
    pad = REGION_PAD * box.height
    area = {"filter_units": "userSpaceOnUse", "x": round(box.x - pad, 3), "y": round(box.y - pad, 3),
            "width": round(box.width + 2 * pad, 3), "height": round(box.height + 2 * pad, 3)}
    return Fit(box.height / REFERENCE_HEIGHT, area)


def loop(element: Element, attribute: str, values: Sequence[str], dur: float, *, discrete: bool = False) -> Element:
    """Append an endless ``<animate>`` of *attribute* through *values* to *element* and return *element*."""
    extra: dict[str, Any] = {"calc_mode": DISCRETE} if discrete else {}
    element.append(Animate(attribute_name=attribute, values=";".join(values), dur=dur, repeat_count=INDEFINITE,
                           **extra))
    return element


def tinted(color: Color | str, alpha: Element | StandardInput, opacity: float = 1.0) -> tuple[FeFlood, FeComposite]:
    """A flood of *color* and its composite inside *alpha*: the glyph shapes painted one color."""
    flood = FeFlood(color, opacity)
    return flood, FeComposite(CompositeOperator.IN, in_=flood, in2=alpha)
