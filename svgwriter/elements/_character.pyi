from collections.abc import Iterator, Mapping, Sequence
from typing import Any, NoReturn
from .._internal._typing import FillRule, LineCap, LineJoin, Opacity
from ..attributes.length import LengthLike
from ..attributes.style import StyleLike
from ..color.paint import PaintValue
from ..pathdata.data import BBox
from ..transform.matrix import Point
from .base import AttrValue, Element
from .shapes import Path
from .text import TSpan, Text

__all__ = ["Character", "CharacterRange"]

class _Characters:
    start: Any
    stop: Any
    text: Any

    def __init__(
        self,
        text: Text,
        start: int,
        stop: int,
    ) -> None: ...
    @property
    def chars(self) -> str: ...
    def bounds(self) -> BBox | None: ...
    def translate(self, dx: float, dy: float = 0.0) -> Any: ...
    def rotate(self, degrees: float) -> Any: ...
    def scale(self, *args: Any, **kwargs: Any) -> NoReturn: ...
    def skew(self, *args: Any, **kwargs: Any) -> NoReturn: ...
    def to_path(self, **kwargs: Any) -> Path: ...
    def wrap(
        self,
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
        **attributes: Any,
    ) -> TSpan: ...
    def __setattr__(self, name: str, value: Any) -> None: ...

class Character(_Characters):
    def __init__(
        self,
        text: Text,
        index: int,
        start: int | None = None,
        stop: int | None = None,
    ) -> None: ...
    @property
    def index(self) -> int: ...
    @property
    def char(self) -> str: ...
    @property
    def position(self) -> Point: ...
    @property
    def angle(self) -> float: ...
    def __repr__(self) -> str: ...

class CharacterRange(_Characters):
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Character]: ...
    def __repr__(self) -> str: ...
