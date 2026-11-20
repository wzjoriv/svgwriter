__all__ = ["CurveCommands"]

class CurveCommands:
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
    ) -> None: ...
    def smooth_curve_to(
        self,
        x2: float,
        y2: float,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...
    def quad_to(
        self,
        x1: float,
        y1: float,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...
    def smooth_quad_to(
        self,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...
    def arc_to(
        self,
        rx: float,
        ry: float,
        rotation: float,
        large_arc: bool,
        sweep: bool,
        x: float,
        y: float,
        *,
        relative: bool = False,
    ) -> None: ...
