from .color import Color

__all__ = ["ColorChannels"]

class ColorChannels:
    r: float
    g: float
    b: float
    a: float

    @property
    def rgb(self) -> tuple[float, float, float]: ...
    @property
    def rgba(self) -> tuple[float, float, float, float]: ...
    @property
    def uint8(self) -> tuple[int, int, int, int]: ...
    @property
    def hex(self) -> str: ...
    @property
    def hsl(self) -> tuple[float, float, float]: ...
    @property
    def opaque(self) -> Color: ...
    @property
    def luminance(self) -> float: ...
