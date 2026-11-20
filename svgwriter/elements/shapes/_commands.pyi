from typing import Any
from ..._internal._typing import Self
from ...pathdata.builder import PathBuilder

__all__ = ["PathCommands"]

class PathCommands:
    def move_to(
        self,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> Self: ...
    def line_to(
        self,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> Self: ...
    def horizontal_to(
        self,
        x: float,
        *,
        relative: bool = False,
    ) -> Self: ...
    def vertical_to(
        self,
        y: float,
        *,
        relative: bool = False,
    ) -> Self: ...
    def curve_to(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> Self: ...
    def smooth_curve_to(
        self,
        x2: float,
        y2: float,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> Self: ...
    def quad_to(
        self,
        x1: float,
        y1: float,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> Self: ...
    def smooth_quad_to(
        self,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> Self: ...
    def arc_to(
        self,
        rx: float,
        ry: float,
        x: float,
        y: float,
        *,
        rotation: float = 0.0,
        large: bool = False,
        clockwise: bool = True,
        relative: bool = False,
    ) -> Self: ...
    def close(self) -> Self: ...
    @classmethod
    def build(cls, builder: PathBuilder, **kwargs: Any) -> Self: ...
