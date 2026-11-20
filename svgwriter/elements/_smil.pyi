from collections.abc import Mapping, Sequence
from typing import Any, Literal
from .._internal._typing import Self
from .animation import Accumulate, Additive, CalcMode
from .base import AttrValue, Child, Element

__all__ = ["FadeShortcut", "SpinShortcut"]

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

class FadeShortcut:
    @classmethod
    def fade(
        cls,
        start: float,
        stop: float,
        **kwargs: Any,
    ) -> Self: ...

class SpinShortcut:
    @classmethod
    def spin(
        cls,
        cx: float = 0,
        cy: float = 0,
        **kwargs: Any,
    ) -> Self: ...
