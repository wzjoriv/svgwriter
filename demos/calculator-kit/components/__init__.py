"""The calculator's parts: keys, the display, the shell styles and the keypad layouts."""

from .display import FONTS, display
from .key import SHAPES, key
from .layouts import LAYOUTS, keypad
from .shell import SHELLS, shell

__all__ = ["FONTS", "LAYOUTS", "SHAPES", "SHELLS", "display", "key", "keypad", "shell"]
