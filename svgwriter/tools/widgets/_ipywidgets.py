"""
The notebook backend: one ipywidgets input per control, the drawing beside them and errors under it.
"""

from __future__ import annotations

import html
from collections.abc import Callable, Mapping
from typing import Any

from ..._internal._platform import missing
from ._choices import Checkbox, ColorPicker, Dropdown, MultiSelect, Segmented, Swatches, Text, Toggle
from ._constants import ERROR_STYLE, IMAGE_STYLE, PANEL_SUMMARY, PANEL_WIDTH, SWATCH_SIZE
from ._control import Control
from ._interact import Changed
from ._numbers import Number, RangeSlider, Slider

__all__ = ["NotebookBackend"]


def _widgets() -> Any:
    try:
        import ipywidgets  # type: ignore[import-untyped]
    except ImportError:
        raise missing("ipywidgets", "svg.interact") from None
    return ipywidgets


def _slider(w: Any, control: Slider | RangeSlider, value: Any) -> tuple[Any, Any]:
    whole = isinstance(value[0] if isinstance(value, tuple) else value, int)
    if isinstance(control, RangeSlider):
        kind = w.IntRangeSlider if whole else w.FloatRangeSlider
        widget = kind(value=value, min=control.min, max=control.max, step=control.step, readout=False)
    else:
        kind = w.IntSlider if whole else w.FloatSlider
        widget = kind(value=value, min=control.min, max=control.max, step=control.step, readout=False)
    readout = w.Label(control.text(value))
    widget.observe(lambda change: setattr(readout, "value", control.text(change.new)), names="value")
    return widget, w.HBox([widget, readout])


def _swatches(w: Any, control: Swatches, value: Any, changed: Callable[[int], None]) -> Any:
    buttons = []
    for position, chip in enumerate(control.chips):
        button = w.Button(tooltip=control.labels[position], layout=w.Layout(width=SWATCH_SIZE, height=SWATCH_SIZE))
        button.style.button_color = chip
        buttons.append(button)

    def pick(position: int) -> None:
        for index, button in enumerate(buttons):
            button.icon = "check" if index == position else ""
        changed(position)

    for position, button in enumerate(buttons):
        button.on_click(lambda _, position=position: pick(position))
    buttons[control.index(value)].icon = "check"
    return w.HBox(buttons)


def _input(w: Any, control: Control, value: Any, send: Callable[[Any], None]) -> Any:
    """The widget for *control* and the box shown for it; edits call ``send(raw)``."""
    if isinstance(control, (Slider, RangeSlider)):
        widget, shown = _slider(w, control, value)
    elif isinstance(control, Swatches):
        return _swatches(w, control, value, send)
    elif isinstance(control, Dropdown):
        options = [(label, position) for position, label in enumerate(control.labels)]
        if isinstance(control, MultiSelect):
            widget = w.SelectMultiple(options=options, value=tuple(control.index(item) for item in value))
            return _observe(widget, lambda raw: send(list(raw)))
        kind = w.ToggleButtons if isinstance(control, Segmented) else w.Dropdown
        widget = shown = kind(options=options, value=control.index(value))
    elif isinstance(control, Checkbox):
        widget = shown = w.Checkbox(value=value, indent=False)
    elif isinstance(control, Toggle):
        widget = shown = w.ToggleButton(value=value, description=control.label or "")
    elif isinstance(control, ColorPicker):
        widget = shown = w.ColorPicker(value=value[:7], concise=False)
    elif isinstance(control, Number):
        widget = shown = (w.IntText if isinstance(value, int) else w.FloatText)(
            value=value, **({"step": control.step} if control.step else {}))
    elif isinstance(control, Text):
        widget = shown = w.Text(value=value)
    else:
        raise TypeError(f"no notebook input for {type(control).__name__}")
    _observe(widget, send)
    return shown


def _observe(widget: Any, send: Callable[[Any], None]) -> Any:
    widget.observe(lambda change: send(change.new), names="value")
    return widget


class NotebookBackend:
    """Controls as ipywidgets in a column, the drawing to their right and the last error under it."""

    def __init__(self) -> None:
        self._w = _widgets()
        self._image = self._w.HTML()
        self._error = self._w.HTML()
        self._box: Any = None
        self._summary = ""

    def panel(self, controls: Mapping[str, Control], values: Mapping[str, Any], changed: Changed) -> None:
        """Build one row per control."""
        w = self._w
        rows = []
        for name, control in controls.items():
            shown = _input(w, control, values[name], lambda raw, name=name: changed(name, raw))
            title = w.Label(control.label or name, layout=w.Layout(min_width="96px"))
            rows.append(w.HBox([title, shown]) if not isinstance(control, Toggle) or isinstance(control, Checkbox)
                        else shown)
        self._summary = PANEL_SUMMARY.format(names=", ".join(c.label or n for n, c in controls.items()))
        column = w.VBox(rows, layout=w.Layout(width=PANEL_WIDTH, min_width=PANEL_WIDTH))
        self._box = w.HBox([column, w.VBox([self._image, self._error])])

    def draw(self, svg: str) -> None:
        """Replace the drawing."""
        self._image.value = f'<div style="{IMAGE_STYLE}">{svg}</div>'

    def fail(self, message: str | None) -> None:
        """Show or clear the error."""
        self._error.value = f'<pre style="{ERROR_STYLE}">{html.escape(message)}</pre>' if message else ""

    def show(self) -> None:
        """Display the panel in the notebook; outside one there is nothing to show.

        The plain-text form, which saved notebooks show without a kernel, names the controls.
        """
        from IPython import get_ipython  # type: ignore[import-not-found]
        from IPython.display import display  # type: ignore[import-not-found]

        if get_ipython() is not None:
            bundle = self._box._repr_mimebundle_()
            display({**bundle, "text/plain": self._summary}, raw=True)
