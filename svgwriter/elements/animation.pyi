from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Literal, TypeAlias
from .._internal._typing import Self
from ..pathdata.builder import PathBuilder
from ..pathdata.data import PathData
from ._mixins import (
    ConditionalAttributes,
    CoreAttributes,
    ExternalResourcesAttribute,
    XLinkAttributes,
    XmlSpace,
)
from .base import AttrValue, Category, Child, ContentModel, Element

__all__ = [
    "Accumulate",
    "Additive",
    "Animate",
    "AnimateColor",
    "AnimateMotion",
    "AnimateTransform",
    "AnimationElement",
    "AnimationFill",
    "CalcMode",
    "Clock",
    "MPath",
    "Restart",
    "Set",
    "TransformType",
]

Clock: TypeAlias = str | float
RepeatCount: TypeAlias = float | Literal['indefinite']

class Restart(str, Enum):
    ALWAYS = 'always'
    WHEN_NOT_ACTIVE = 'whenNotActive'
    NEVER = 'never'

class AnimationFill(str, Enum):
    FREEZE = 'freeze'
    REMOVE = 'remove'

class CalcMode(str, Enum):
    DISCRETE = 'discrete'
    LINEAR = 'linear'
    PACED = 'paced'
    SPLINE = 'spline'

class Additive(str, Enum):
    REPLACE = 'replace'
    SUM = 'sum'

class Accumulate(str, Enum):
    NONE = 'none'
    SUM = 'sum'

class TransformType(str, Enum):
    TRANSLATE = 'translate'
    SCALE = 'scale'
    ROTATE = 'rotate'
    SKEW_X = 'skewX'
    SKEW_Y = 'skewY'

class AnimationElement(XLinkAttributes, ConditionalAttributes, ExternalResourcesAttribute, CoreAttributes, category=Category.ANIMATION):
    def __init__(
        self,
        *args: Child,
        begin: Clock | None = None,
        dur: Clock | None = None,
        end: Clock | None = None,
        min: Clock | None = None,
        max: Clock | None = None,
        restart: Restart = Restart.ALWAYS,
        repeat_count: RepeatCount | None = None,
        repeat_dur: Clock | None = None,
        fill: AnimationFill | None = None,
        href: str | Element | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class _AttributeTarget(Element):
    def __init__(
        self,
        *args: Child,
        attribute_name: str | None = None,
        attribute_type: Literal['CSS', 'XML', 'auto'] | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class _ValueAnimation(Element):
    def __init__(
        self,
        *args: Child,
        values: Sequence[Any] | str | None = None,
        from_: Any = None,
        to: Any = None,
        by: Any = None,
        calc_mode: CalcMode | None = None,
        key_times: Sequence[float] | str | None = None,
        key_splines: Sequence[tuple[float, float, float, float]] | str | None = None,
        additive: Additive | None = None,
        accumulate: Accumulate | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class Animate(AnimationElement, _ValueAnimation, _AttributeTarget, tag='animate'):
    @classmethod
    def fade(
        cls,
        start: float,
        stop: float,
        *,
        begin: Clock | None = None,
        dur: Clock | None = None,
        end: Clock | None = None,
        min: Clock | None = None,
        max: Clock | None = None,
        restart: Restart = Restart.ALWAYS,
        repeat_count: RepeatCount | None = None,
        repeat_dur: Clock | None = None,
        fill: AnimationFill | None = None,
        href: str | Element | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Self: ...

class Set(AnimationElement, _AttributeTarget, tag='set'):
    def __init__(
        self,
        attribute_name: str | None = None,
        to: Any = None,
        *,
        begin: Clock | None = None,
        dur: Clock | None = None,
        end: Clock | None = None,
        min: Clock | None = None,
        max: Clock | None = None,
        restart: Restart = Restart.ALWAYS,
        repeat_count: RepeatCount | None = None,
        repeat_dur: Clock | None = None,
        fill: AnimationFill | None = None,
        href: str | Element | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        attribute_type: Literal['CSS', 'XML', 'auto'] | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class AnimateColor(AnimationElement, _ValueAnimation, _AttributeTarget, tag='animateColor'):
    ...

class AnimateTransform(AnimationElement, _ValueAnimation, _AttributeTarget, tag='animateTransform'):
    def __init__(
        self,
        type: TransformType = TransformType.TRANSLATE,
        *,
        begin: Clock | None = None,
        dur: Clock | None = None,
        end: Clock | None = None,
        min: Clock | None = None,
        max: Clock | None = None,
        restart: Restart = Restart.ALWAYS,
        repeat_count: RepeatCount | None = None,
        repeat_dur: Clock | None = None,
        fill: AnimationFill | None = None,
        href: str | Element | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        values: Sequence[Any] | str | None = None,
        from_: Any = None,
        to: Any = None,
        by: Any = None,
        calc_mode: CalcMode | None = None,
        key_times: Sequence[float] | str | None = None,
        key_splines: Sequence[tuple[float, float, float, float]] | str | None = None,
        additive: Additive | None = None,
        accumulate: Accumulate | None = None,
        attribute_name: str | None = None,
        attribute_type: Literal['CSS', 'XML', 'auto'] | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @classmethod
    def spin(
        cls,
        cx: float = 0,
        cy: float = 0,
        *,
        begin: Clock | None = None,
        dur: Clock | None = None,
        end: Clock | None = None,
        min: Clock | None = None,
        max: Clock | None = None,
        restart: Restart = Restart.ALWAYS,
        repeat_count: RepeatCount | None = None,
        repeat_dur: Clock | None = None,
        fill: AnimationFill | None = None,
        href: str | Element | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        values: Sequence[Any] | str | None = None,
        by: Any = None,
        calc_mode: CalcMode | None = None,
        key_times: Sequence[float] | str | None = None,
        key_splines: Sequence[tuple[float, float, float, float]] | str | None = None,
        additive: Additive | None = None,
        accumulate: Accumulate | None = None,
        attribute_name: str | None = None,
        attribute_type: Literal['CSS', 'XML', 'auto'] | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Self: ...

class MPath(XLinkAttributes, ExternalResourcesAttribute, CoreAttributes, tag='mpath', category=Category.ANIMATION):
    def __init__(
        self,
        href: str | Element | None = None,
        *,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...

class AnimateMotion(AnimationElement, _ValueAnimation, tag='animateMotion', content=ContentModel.ELEMENTS):
    def __init__(
        self,
        *children: Child,
        path: PathData | PathBuilder | str | None = None,
        key_points: Sequence[float] | str | None = None,
        rotate: float | Literal['auto', 'auto-reverse'] | None = None,
        origin: str | None = None,
        begin: Clock | None = None,
        dur: Clock | None = None,
        end: Clock | None = None,
        min: Clock | None = None,
        max: Clock | None = None,
        restart: Restart = Restart.ALWAYS,
        repeat_count: RepeatCount | None = None,
        repeat_dur: Clock | None = None,
        fill: AnimationFill | None = None,
        href: str | Element | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        external_resources_required: bool | None = None,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        values: Sequence[Any] | str | None = None,
        from_: Any = None,
        to: Any = None,
        by: Any = None,
        calc_mode: CalcMode | None = None,
        key_times: Sequence[float] | str | None = None,
        key_splines: Sequence[tuple[float, float, float, float]] | str | None = None,
        additive: Additive | None = None,
        accumulate: Accumulate | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
