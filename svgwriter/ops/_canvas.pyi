import skia
from numpy import ndarray
from skia import Canvas, Surface
from ..color.color import ColorLike

__all__ = ["make_surface", "paint_svg", "read_pixels"]

def make_surface(
    width: float,
    height: float,
    scale: float,
    background: ColorLike | None,
) -> skia.Surface: ...

def paint_svg(
    canvas: Canvas,
    text: str,
    width: float,
    height: float,
) -> None: ...

def read_pixels(surface: Surface) -> ndarray: ...
