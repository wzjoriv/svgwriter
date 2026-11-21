"""
The preview page's controls: one labelled HTML input per declared control, read back by the page's script.
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
from ._constants import OPTION_CHARACTER, OPTION_PADDING

__all__ = ["controls_form", "readouts"]


def _attributes(**values: Any) -> str:
    return "".join(f' {key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in values.items()
                   if value is not None and value is not False)


def _labelled(name: str) -> str:
    return _attributes(aria_labelledby=f"label-{name}")


def _range(name: str, control: Slider | RangeSlider, value: float) -> str:
    bounds = _attributes(min=control.min, max=control.max, step=control.step, value=value)
    return f"<input type='range'{bounds}{_labelled(name)}>"


def _radios(name: str, control: Dropdown, value: Any, chips: tuple[str, ...] | None = None) -> str:
    chosen = control.index(value)
    buttons = []
    for position, label in enumerate(control.labels):
        mark = (f"<span class='chip' style='background:{chips[position]}' title='{html.escape(label)}'></span>"
                if chips else html.escape(label))
        named = _attributes(aria_label=label) if chips else ""
        radio = (f"<input type='radio'{_attributes(name=f'field-{name}', value=position, checked=position == chosen)}"
                 f"{named}>")
        buttons.append(f"<label>{radio}{mark}</label>")
    if chips:
        return f"<span class='segmented swatches' role='radiogroup'{_labelled(name)}>{''.join(buttons)}</span>"
    widest = max(map(len, control.labels), default=0) * OPTION_CHARACTER
    style = f" style='--option:calc({widest:.1f}ch + {OPTION_PADDING}px)'"
    return f"<span class='segmented' role='radiogroup'{style}{_labelled(name)}>{''.join(buttons)}</span>"


def _options(name: str, control: Dropdown, chosen: set[int], multiple: bool) -> str:
    items = "".join(f"<option{_attributes(value=position, selected=position in chosen)}>{html.escape(label)}</option>"
                    for position, label in enumerate(control.labels))
    return f"<select{' multiple' if multiple else ''}{_labelled(name)}>{items}</select>"


def _input(name: str, control: Control, value: Any) -> tuple[str, str]:
    """``(kind, inputs)``: how the script reads the field and its HTML."""
    if isinstance(control, RangeSlider):
        return "pair", _range(name, control, value[0]) + _range(name, control, value[1])
    if isinstance(control, Slider):
        return "number", _range(name, control, value)
    if isinstance(control, Number):
        bounds = _attributes(min=control.min, max=control.max, step=control.step or "any", value=value)
        return "number", f"<input type='number'{bounds}{_labelled(name)}>"
    if isinstance(control, Toggle):
        style = "" if isinstance(control, Checkbox) else " class='switch'"
        return "bool", f"<input type='checkbox'{style}{_attributes(checked=bool(value))}{_labelled(name)}>"
    if isinstance(control, Swatches):
        return "index", _radios(name, control, value, control.chips)
    if isinstance(control, MultiSelect):
        return "indices", _options(name, control, {control.index(item) for item in value}, multiple=True)
    if isinstance(control, Segmented) and control.compact:
        return "index", _radios(name, control, value)
    if isinstance(control, Dropdown):
        return "index", _options(name, control, {control.index(value)}, multiple=False)
    if isinstance(control, ColorPicker):
        return "text", f"<input type='color'{_attributes(value=value[:7])}{_labelled(name)}>"
    if isinstance(control, Text):
        return "text", f"<input type='text'{_attributes(value=value)}{_labelled(name)}>"
    raise TypeError(f"no preview input for {type(control).__name__}")


def readouts(controls: Mapping[str, Control], values: Mapping[str, Any]) -> dict[str, str]:
    """The readout text of every control at *values* (starting values where missing)."""
    return {name: control.text(values.get(name, control.initial)) for name, control in controls.items()}


def controls_form(controls: Mapping[str, Control], values: Mapping[str, Any]) -> str:
    """The controls as a form starting at *values*, one labelled group per control; empty without controls."""
    if not controls:
        return ""
    shown = readouts(controls, values)
    fields = []
    for name, control in controls.items():
        kind, inputs = _input(name, control, values.get(name, control.initial))
        fields.append(f"<div class='field' role='group'{_attributes(data_name=name, data_kind=kind)}{_labelled(name)}>"
                      f"<div class='head'><span class='name'{_attributes(id=f'label-{name}')}>"
                      f"{html.escape(control.label or name)}</span><output>{html.escape(shown[name])}</output></div>"
                      f"{inputs}</div>")
    return f"<form class='svgwriter-controls'>{''.join(fields)}</form>"
