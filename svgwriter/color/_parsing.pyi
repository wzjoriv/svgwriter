from .color import Color

__all__ = ["color_function"]

def color_function(
    kind: str,
    body: str,
    text: str,
) -> Color: ...
