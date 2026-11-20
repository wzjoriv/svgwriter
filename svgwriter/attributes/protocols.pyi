from typing import Protocol, runtime_checkable

__all__ = ["SupportsSVG", "TextSink"]

@runtime_checkable
class SupportsSVG(Protocol):
    def svg_value(self, precision: int = ...) -> str: ...

@runtime_checkable
class TextSink(Protocol):
    def write(self, text: str, /) -> object: ...
