from typing import Any
from .core import Element

__all__ = ["Motion"]

class Motion:
    element: Element

    def __init__(self, element: Element) -> None: ...
    def tween(
        self,
        attribute: str,
        start: Any,
        end: Any,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def fade_in(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def fade_out(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def draw(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def wipe(
        self,
        side: str = 'left',
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def typewriter(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
    ) -> Motion: ...
    def grow(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def shrink(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def pulse(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = 'indefinite',
        scale: float = 1.1,
    ) -> Motion: ...
    def spin(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        turns: float = 1.0,
        freeze: bool = True,
    ) -> Motion: ...
    def slide_in(
        self,
        side: str = 'left',
        dur: float = 1.0,
        *,
        distance: float = 100.0,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def move_to(
        self,
        x: float,
        y: float,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def follow(
        self,
        path: Any,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        rotate: bool = True,
        freeze: bool = True,
    ) -> Motion: ...
    def shake(
        self,
        dur: float = 0.5,
        *,
        begin: float = 0.0,
        distance: float = 4.0,
        repeat: float | str | None = None,
    ) -> Motion: ...
    def bounce(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        height: float = 20.0,
        repeat: float | str | None = None,
    ) -> Motion: ...
    def blink(
        self,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = 'indefinite',
    ) -> Motion: ...
    def color_cycle(
        self,
        colors: list[Any],
        dur: float = 1.0,
        *,
        attribute: str = 'fill',
        begin: float = 0.0,
        repeat: float | str | None = 'indefinite',
    ) -> Motion: ...
    def morph(
        self,
        target: Element,
        dur: float = 1.0,
        *,
        begin: float = 0.0,
        repeat: float | str | None = None,
        freeze: bool = True,
    ) -> Motion: ...
    def stagger(
        self,
        preset: str,
        step: float = 0.2,
        *,
        begin: float = 0.0,
        **options: Any,
    ) -> Motion: ...
