"""Live controls for drawing functions: notebook panels, preview forms and parameter sweeps.

A control is pure data (:class:`Slider`, :class:`Segmented`, :class:`ColorPicker`, ...), so one declaration
drives a notebook panel (:func:`interact`, the ``widget`` extra), the form of ``svgwriter preview`` and an
animation over time (:func:`sweep`). Shorthands stand in for controls: ``(0, 10)`` is a slider,
``["a", "b"]`` a row of buttons, ``True`` a toggle and ``"#ff6347"`` a colour picker.

Example
-------
>>> import svgwriter as svg
>>> @svg.widgets.controls(radius=(0, 30), color=["tomato", "gold", "teal"])
... def dot(radius=10, color="tomato"):
...     return svg.circle(30, 30, radius, fill=color)
>>> view = svg.interact(dot, backend=svg.widgets.Recorder())  # a panel in a notebook
>>> view.update(radius=25).code()
"dot(radius=25, color='tomato')"
>>> svg.sweep(dot, radius=(5, 30), dur=1).values_at(0.5)
{'color': 'tomato', 'radius': 18}
"""

from __future__ import annotations

from ._choices import Checkbox, ColorPicker, Dropdown, MultiSelect, Segmented, Swatches, Text, Toggle
from ._control import Control
from ._infer import control, controls, controls_of
from ._interact import Backend, Interactive, interact
from ._numbers import IntSlider, Number, RangeSlider, Slider
from ._recorder import Recorder
from ._sweep import Sweep, sweep

__all__ = [
    "Backend",
    "Checkbox",
    "ColorPicker",
    "Control",
    "Dropdown",
    "IntSlider",
    "Interactive",
    "MultiSelect",
    "Number",
    "RangeSlider",
    "Recorder",
    "Segmented",
    "Slider",
    "Sweep",
    "Swatches",
    "Text",
    "Toggle",
    "control",
    "controls",
    "controls_of",
    "interact",
    "sweep",
]
