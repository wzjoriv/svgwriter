from collections.abc import Callable
from dataclasses import dataclass
from typing import Final
from ._reading import RGB, Shape

__all__ = ["COLOR_MODELS", "OPTIONS"]

COLOR_MODELS: Final[dict[str, Callable[[str], tuple[float, ...]]]]

@dataclass
class _Style:
    fill: bool
    draw: bool
    colors: dict[str, RGB]
    color: RGB = (0.0, 0.0, 0.0)
    text_color: RGB | None = None
    fill_color: RGB | None = None
    draw_color: RGB | None = None
    fill_opacity: float = 1.0
    draw_opacity: float = 1.0
    line_width: float = 0.4
    linecap: str = 'butt'
    linejoin: str = 'miter'
    miter_limit: float = 10.0
    evenodd: bool = False
    dashes: tuple[float, ...] = ()

    def __init__(
        self,
        fill: bool,
        draw: bool,
        colors: dict[str, RGB],
        color: RGB = (0.0, 0.0, 0.0),
        text_color: RGB | None = None,
        fill_color: RGB | None = None,
        draw_color: RGB | None = None,
        fill_opacity: float = 1.0,
        draw_opacity: float = 1.0,
        line_width: float = 0.4,
        linecap: str = 'butt',
        linejoin: str = 'miter',
        miter_limit: float = 10.0,
        evenodd: bool = False,
        dashes: tuple[float, ...] = (),
    ) -> None: ...
    def paint(self, key: str, value: str | None) -> None: ...
    def shape(self, ops: list) -> Shape: ...

OPTIONS: Final[dict[str, Callable[[_Style, str | None], None]]]
