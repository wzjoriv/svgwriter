"""
Controls that pick: on/off switches, one option, several options, colours and text.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ...model.color import Color, parse_color
from ._constants import DEFAULT_COLOR
from ._control import Control

__all__ = ["Checkbox", "ColorPicker", "Dropdown", "MultiSelect", "Segmented", "Swatches", "Text", "Toggle",
           "hex_color"]


def hex_color(value: Any) -> str:
    """*value* (a colour name, CSS syntax or :class:`~svgwriter.Color`) as ``#rrggbb`` or ``#rrggbbaa``."""
    if isinstance(value, Color):
        return value.hex
    try:
        return parse_color(value).hex
    except (ValueError, TypeError) as error:
        raise ValueError(f"not a colour: {value!r}") from error


@dataclass(frozen=True)
class Toggle(Control):
    """On or off, shown as a switch button.

    Parameters
    ----------
    value : bool, optional
        The starting state. Defaults to False.
    label : str, optional
        Shown on the button.

    See Also
    --------
    Checkbox : The same as a box to tick.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.widgets.Toggle(True).initial
    True
    """

    value: bool = False

    def check(self, value: Any) -> bool:
        if not isinstance(value, bool):
            raise TypeError(f"expected True or False, got {value!r}")
        return value

    def _default(self) -> bool:
        return self.value

    def text(self, value: Any) -> str:
        return "on" if value else "off"


@dataclass(frozen=True)
class Checkbox(Toggle):
    """On or off, shown as a box to tick.

    Parameters
    ----------
    value : bool, optional
        The starting state. Defaults to False.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.widgets.Checkbox().check(True)
    True
    """


def _pairs(options: Sequence[Any] | Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    pairs = tuple(options.items()) if isinstance(options, Mapping) else tuple((str(o), o) for o in options)
    if not pairs:
        raise ValueError("options must not be empty")
    return pairs


@dataclass(frozen=True)
class Dropdown(Control):
    """One of several options, from a menu.

    Parameters
    ----------
    options : sequence or mapping
        The choices, or ``{label: value}``.
    value : object, optional
        The starting choice. Defaults to the first.
    label : str, optional
        Shown beside the menu.

    Raises
    ------
    ValueError
        If there are no options or `value` is not one of them.

    See Also
    --------
    Segmented : The same as a row of buttons.

    Examples
    --------
    >>> import svgwriter as svg
    >>> weight = svg.widgets.Dropdown({"light": 300, "bold": 700})
    >>> weight.initial, weight.labels
    (300, ('light', 'bold'))
    """

    options: Sequence[Any] | Mapping[str, Any]
    value: Any = None

    choices: tuple[tuple[str, Any], ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "choices", _pairs(self.options))
        if self.value is not None:
            self.check(self.value)

    @property
    def labels(self) -> tuple[str, ...]:
        """The options' labels, in order."""
        return tuple(label for label, _ in self.choices)

    @property
    def values(self) -> tuple[Any, ...]:
        """The options' values, in order."""
        return tuple(value for _, value in self.choices)

    def index(self, value: Any) -> int:
        """The position of *value* among the options.

        Parameters
        ----------
        value : object
            One of the options' values.

        Returns
        -------
        int
            Its index.

        Raises
        ------
        ValueError
            If it is not an option.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.widgets.Segmented(["S", "M", "L"]).index("L")
        2
        """
        for position, option in enumerate(self.values):
            if option is value or option == value and isinstance(option, bool) == isinstance(value, bool):
                return position
        raise ValueError(f"{value!r} is not one of {list(self.values)!r}")

    def check(self, value: Any) -> Any:
        return self.values[self.index(value)]

    def from_form(self, raw: Any) -> Any:
        if isinstance(raw, bool) or not isinstance(raw, int) or not 0 <= raw < len(self.choices):
            raise ValueError(f"no option {raw!r}")
        return self.values[raw]

    def _default(self) -> Any:
        return self.values[0]

    def text(self, value: Any) -> str:
        return self.labels[self.index(value)]


@dataclass(frozen=True)
class Segmented(Dropdown):
    """One of a few options, as a row of buttons.

    Parameters
    ----------
    options : sequence or mapping
        The choices, or ``{label: value}``.
    value : object, optional
        The starting choice. Defaults to the first.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.widgets.Segmented(["♠", "♥"]).from_form(1)
    '♥'
    """


@dataclass(frozen=True)
class Swatches(Dropdown):
    """One of several colours, as a row of colour chips.

    Parameters
    ----------
    options : sequence of colour
        The colours, as given to the drawing function.
    value : colour, optional
        The starting colour. Defaults to the first.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.widgets.Swatches(["tomato", "#0ea5e9"]).chips
    ('#ff6347', '#0ea5e9')
    """

    def __post_init__(self) -> None:
        super().__post_init__()
        for color in self.values:
            hex_color(color)

    @property
    def chips(self) -> tuple[str, ...]:
        """The colours as ``#rrggbb``, for drawing the chips."""
        return tuple(hex_color(color) for color in self.values)


@dataclass(frozen=True)
class MultiSelect(Dropdown):
    """Any number of options; the value is a tuple in option order.

    Parameters
    ----------
    options : sequence or mapping
        The choices, or ``{label: value}``.
    value : sequence, optional
        The starting choices. Defaults to none.

    Examples
    --------
    >>> import svgwriter as svg
    >>> layers = svg.widgets.MultiSelect(["grid", "guides", "labels"], value=["labels", "grid"])
    >>> layers.initial, layers.from_form([1])
    (('grid', 'labels'), ('guides',))
    """

    value: Sequence[Any] = ()

    def check(self, value: Any) -> tuple[Any, ...]:
        if isinstance(value, (str, bytes)) or not isinstance(value, (Sequence, set, frozenset)):
            raise TypeError(f"expected a sequence of options, got {value!r}")
        chosen = {self.index(item) for item in value}
        return tuple(self.values[position] for position in sorted(chosen))

    def from_form(self, raw: Any) -> tuple[Any, ...]:
        if not isinstance(raw, list):
            raise ValueError(f"expected a list of option indices, got {raw!r}")
        return self.check([Dropdown.from_form(self, item) for item in raw])

    def _default(self) -> tuple[Any, ...]:
        return ()

    def text(self, value: Any) -> str:
        return ", ".join(self.labels[self.index(item)] for item in value) or "none"


@dataclass(frozen=True)
class ColorPicker(Control):
    """Any colour; the drawing function receives it as ``#rrggbb`` (``#rrggbbaa`` when translucent).

    Parameters
    ----------
    value : str or Color, optional
        The starting colour. Defaults to black.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.widgets.ColorPicker("tomato").initial
    '#ff6347'
    """

    value: Any = DEFAULT_COLOR

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", hex_color(self.value))

    def check(self, value: Any) -> str:
        return hex_color(value)

    def _default(self) -> str:
        return self.value


@dataclass(frozen=True)
class Text(Control):
    """A line of text.

    Parameters
    ----------
    value : str, optional
        The starting text. Defaults to ``""``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.widgets.Text("Hello").initial
    'Hello'
    """

    value: str = ""

    def check(self, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError(f"expected text, got {type(value).__name__}")
        return value

    def _default(self) -> str:
        return self.value
