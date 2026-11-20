from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, TypeVar, overload
from ._document.ingest import SupportsSVG
from ._document.output import Output
from ._document.sizing import Sizing
from ._internal._typing import AnyPath, FillRule, LineCap, LineJoin, Opacity, Self
from .attributes.length import LengthLike
from .attributes.style import StyleLike, StyleSheet
from .attributes.viewbox import PreserveAspectRatio
from .color.paint import PaintValue
from .elements._factory import ElementFactory
from .elements._mixins import XmlSpace
from .elements._viewport import ViewBoxLike
from .elements.base import AttrValue, Element
from .elements.structure import Defs, Desc, Group, StyleElement, Svg, Title
from .io.parser import Strictness

__all__ = ["Document"]

E = TypeVar('E', bound=Element)

class Document(Sizing, Output, ElementFactory):
    root: Svg | None

    def __init__(
        self,
        width: float | None = None,
        height: float | None = None,
        *,
        root: Svg | None = None,
        version: str | None = '1.1',
        base_profile: str | None = None,
        zoom_and_pan: str | None = None,
        content_style_type: str | None = None,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        view_box: ViewBoxLike | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        external_resources_required: bool | None = None,
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
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @classmethod
    def from_string(
        cls,
        text: str | bytes,
        *,
        strictness: Strictness | None = None,
    ) -> Document: ...
    @classmethod
    @contextmanager
    def writing(
        cls,
        path: AnyPath,
        width: float,
        height: float,
        *,
        options=None,
        root: Svg | None = None,
        version: str | None = '1.1',
        base_profile: str | None = None,
        zoom_and_pan: str | None = None,
        content_style_type: str | None = None,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        view_box: ViewBoxLike | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        external_resources_required: bool | None = None,
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
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Iterator[Document]: ...
    @property
    def current(self) -> Element: ...
    @property
    def defs(self) -> Defs: ...
    @defs.setter
    def defs(self, value: Defs) -> None: ...
    @overload
    def add(self, element: E) -> E: ...
    @overload
    def add(self, element: SupportsSVG) -> Group: ...
    def define(self, element: E) -> E: ...
    def title(self, text: str) -> Title: ...
    def describe(self, text: str) -> Desc: ...
    def style(
        self,
        css: str | StyleSheet = '',
        *,
        type: str = 'text/css',
        media: str | None = None,
        title: str | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> StyleElement: ...
    @contextmanager
    def nest(self, element: E) -> Iterator[E]: ...
    def __iadd__(self, elements: Element | SupportsSVG | Iterable[Element]) -> Self: ...
    def __iter__(self) -> Iterator[Element]: ...
    def __len__(self) -> int: ...
    @overload
    def __getitem__(self, key: int) -> Element: ...
    @overload
    def __getitem__(self, key: slice) -> list[Element]: ...
    @overload
    def __getitem__(self, key: str) -> Element: ...
    def __setitem__(self, key: int | str, element: Element) -> None: ...
    def __contains__(self, item: object) -> bool: ...
    def get_element_by_id(self, element_id: str) -> Element | None: ...
