from collections.abc import Mapping, Sequence
from typing import Any
from ...attributes.style import StyleLike
from .._mixins import CoreAttributes, StyleAttributes, XmlSpace
from ..base import AttrValue, Category, Child, ContentModel

__all__ = ["Desc", "Metadata", "Title"]

class _Descriptive(StyleAttributes, CoreAttributes, category=Category.DESCRIPTIVE, content=ContentModel.TEXT):
    def __init__(
        self,
        text: str = '',
        *,
        class_: str | Sequence[str] | None = None,
        style: StyleLike | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class Desc(_Descriptive, tag='desc'):
    ...

class Title(_Descriptive, tag='title'):
    ...

class Metadata(CoreAttributes, tag='metadata', category=Category.DESCRIPTIVE, content=ContentModel.MIXED):
    def __init__(
        self,
        *children: Child,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
