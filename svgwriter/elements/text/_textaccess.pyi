from collections.abc import Iterator, Mapping, Sequence
from typing import Any, overload
from ..._internal._typing import FillRule, LineCap, LineJoin, Opacity
from ...attributes.length import LengthLike
from ...attributes.style import StyleLike
from ...color.paint import PaintValue
from ...ops.text import GlyphBox
from ...pathdata.data import BBox, PathData
from ..core._element import AttrValue, Element
from ..shapes import Path
from ..structure import Group
from ._character import Character, CharacterRange
from ._text import TSpan

__all__ = ["TextAccess"]

class TextAccess:
    @property
    def characters(self) -> str: ...
    def layout(self) -> list[GlyphBox]: ...
    def local_bbox(self) -> BBox | None: ...
    def local_outline(self) -> PathData: ...
    def __len__(self) -> int: ...
    @overload
    def __getitem__(self, index: int) -> Character: ...
    @overload
    def __getitem__(self, index: slice) -> CharacterRange: ...
    def __iter__(self) -> Iterator[Character]: ...
    def run_style(self, source: Element) -> dict[str, object]: ...
    def runs(self) -> list[Path]: ...
    def glyphs(self, *, skip_blank: bool = False) -> Group: ...
    def span(
        self,
        text: str,
        *,
        fill: PaintValue = None,
        fill_opacity: Opacity | None = None,
        fill_rule: FillRule | None = None,
        stroke: PaintValue = None,
        stroke_width: LengthLike | None = None,
        stroke_opacity: Opacity | None = None,
        stroke_linecap: LineCap | None = None,
        stroke_linejoin: LineJoin | None = None,
        stroke_miterlimit: float | None = None,
        stroke_dasharray: Sequence[float] | str | None = None,
        stroke_dashoffset: LengthLike | None = None,
        opacity: Opacity | None = None,
        display: str | None = None,
        visibility: str | None = None,
        color: str | None = None,
        clip_path: str | Element | None = None,
        mask: str | Element | None = None,
        filter: str | Element | None = None,
        font_family: str | None = None,
        font_size: LengthLike | None = None,
        font_weight: str | int | None = None,
        text_anchor: str | None = None,
        class_: str | Sequence[str] | None = None,
        style: StyleLike | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> TSpan: ...
