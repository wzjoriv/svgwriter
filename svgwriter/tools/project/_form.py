"""
The preview page's controls: one plain HTML input per declared control, read back by a small script.
"""

from __future__ import annotations

import html
from collections.abc import Mapping
from typing import Any

from ..widgets import (
    Checkbox,
    ColorPicker,
    Control,
    Dropdown,
    MultiSelect,
    Number,
    RangeSlider,
    Segmented,
    Slider,
    Swatches,
    Text,
    Toggle,
)
from ._constants import FORM_SCRIPT, FORM_STYLE, POST_MILLISECONDS

__all__ = ["controls_form", "readouts"]


def _attributes(**values: Any) -> str:
    return "".join(f' {key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in values.items()
                   if value is not None and value is not False)


def _range(control: Slider | RangeSlider, value: float) -> str:
    return f"<input type='range'{_attributes(min=control.min, max=control.max, step=control.step, value=value)}>"


def _radios(name: str, control: Dropdown, value: Any, chips: tuple[str, ...] | None = None) -> str:
    chosen = control.index(value)
    buttons = []
    for position, label in enumerate(control.labels):
        mark = (f"<span class='chip' style='background:{chips[position]}' title='{html.escape(label)}'></span>"
                if chips else html.escape(label))
        radio = f"<input type='radio'{_attributes(name=f'field-{name}', value=position, checked=position == chosen)}>"
        buttons.append(f"<label>{radio}{mark}</label>")
    return f"<span class='segmented'>{''.join(buttons)}</span>"


def _options(control: Dropdown, chosen: set[int], multiple: bool) -> str:
    items = "".join(f"<option{_attributes(value=position, selected=position in chosen)}>{html.escape(label)}</option>"
                    for position, label in enumerate(control.labels))
    return f"<select{' multiple' if multiple else ''}>{items}</select>"


def _input(name: str, control: Control, value: Any) -> tuple[str, str]:
    """``(kind, inputs)``: how the script reads the field and its HTML."""
    if isinstance(control, RangeSlider):
        return "pair", _range(control, value[0]) + _range(control, value[1])
    if isinstance(control, Slider):
        return "number", _range(control, value)
    if isinstance(control, Number):
        bounds = _attributes(min=control.min, max=control.max, step=control.step or "any", value=value)
        return "number", f"<input type='number'{bounds}>"
    if isinstance(control, Toggle):
        style = "" if isinstance(control, Checkbox) else " class='switch'"
        return "bool", f"<input type='checkbox'{style}{_attributes(checked=bool(value))}>"
    if isinstance(control, Swatches):
        return "index", _radios(name, control, value, control.chips)
    if isinstance(control, MultiSelect):
        return "indices", _options(control, {control.index(item) for item in value}, multiple=True)
    if isinstance(control, Segmented):
        return "index", _radios(name, control, value)
    if isinstance(control, Dropdown):
        return "index", _options(control, {control.index(value)}, multiple=False)
    if isinstance(control, ColorPicker):
        return "text", f"<input type='color'{_attributes(value=value[:7])}>"
    if isinstance(control, Text):
        return "text", f"<input type='text'{_attributes(value=value)}>"
    raise TypeError(f"no preview input for {type(control).__name__}")


def readouts(controls: Mapping[str, Control], values: Mapping[str, Any]) -> dict[str, str]:
    """The readout text of every control at *values* (starting values where missing)."""
    return {name: control.text(values.get(name, control.initial)) for name, control in controls.items()}


def controls_form(controls: Mapping[str, Control], values: Mapping[str, Any]) -> str:
    """The controls as a form, starting at *values*; it posts every change to ``/values``."""
    if not controls:
        return ""
    shown = readouts(controls, values)
    fields = []
    for name, control in controls.items():
        kind, inputs = _input(name, control, values.get(name, control.initial))
        fields.append(f"<div class='field'{_attributes(data_name=name, data_kind=kind)}>"
                      f"<span class='name'>{html.escape(control.label or name)}</span>{inputs}"
                      f"<output>{html.escape(shown[name])}</output></div>")
    script = FORM_SCRIPT.replace("{delay}", str(POST_MILLISECONDS))
    return f"<form class='svgwriter-controls'><style>{FORM_STYLE}</style>{''.join(fields)}</form>{script}"
