"""
Controls from shorthand (``(0, 10)``, ``["a", "b"]``, ``True``, ``"#ff0000"``), the ``@controls`` declaration and
the controls a function ends up with.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping, Sequence
from numbers import Real
from typing import Any, TypeVar

from ...model.color import Color
from ...model.units import Length
from ._choices import ColorPicker, Dropdown, Segmented, Swatches, Text, Toggle, hex_color
from ._constants import CONTROLS_ATTRIBUTE, SEGMENTED_MAX, SLIDER_SPAN
from ._control import Control
from ._numbers import IntSlider, Slider

__all__ = ["accepts", "control", "controls", "controls_of", "is_color"]

F = TypeVar("F", bound=Callable[..., Any])


def is_color(value: Any) -> bool:
    """Whether *value* is a :class:`~svgwriter.Color` or a ``#``-colour string."""
    if isinstance(value, Color):
        return True
    if not isinstance(value, str) or not value.startswith("#"):
        return False
    try:
        hex_color(value)
    except ValueError:
        return False
    return True


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _slider(low: Any, high: Any, step: Any = None, value: Any = None, label: str | None = None) -> Slider:
    ends = (low, high)
    if all(isinstance(end, Length) for end in ends):
        if low.unit != high.unit:
            raise ValueError(f"slider ends need one unit, got {low} and {high}")
        unit = low.unit.value
        return Slider(low.value, high.value, step, value, label=label, units=unit)
    if not all(_is_number(end) for end in ends):
        raise TypeError(f"slider ends must be numbers or lengths, got {low!r} and {high!r}")
    whole = all(isinstance(part, int) for part in (low, high, step if step is not None else 1))
    kind = IntSlider if whole else Slider
    return kind(low, high, step, value, label=label)


def _around(value: float | Length, label: str | None) -> Slider:
    number = value.value if isinstance(value, Length) else value
    low, high = (0, SLIDER_SPAN * number) if number > 0 else (SLIDER_SPAN * number, 0) if number < 0 else (0, 1)
    if isinstance(value, Length):
        return Slider(low, high, value=number, label=label, units=value.unit.value)
    if isinstance(value, int):
        return IntSlider(int(low), int(high), value=value, label=label)
    return Slider(float(low), float(high), value=value, label=label)


def control(spec: Any, *, label: str | None = None) -> Control:
    """The control a shorthand stands for.

    ===========================================  ==========================================
    Shorthand                                    Control
    ===========================================  ==========================================
    a :class:`Control`                           itself
    ``True`` / ``False``                         :class:`Toggle`
    ``(0, 10)``, ``(0, 1, 0.1)``                 :class:`Slider` (:class:`IntSlider` for ints)
    ``(svg.mm(0), svg.mm(20))``                  :class:`Slider` in millimetres
    ``40``, ``0.5``, ``svg.mm(5)``               a slider from 0 to twice the value
    ``"#ff6347"``, a :class:`~svgwriter.Color`   :class:`ColorPicker`
    any other str                                :class:`Text`
    ``["a", "b"]``, ``{"label": value}``         :class:`Segmented` up to 4 options, else :class:`Dropdown`
    a list of colours                            :class:`Swatches`
    ===========================================  ==========================================

    Parameters
    ----------
    spec : object
        The shorthand.
    label : str, optional
        A label for the control. Defaults to None.

    Returns
    -------
    Control
        The control.

    Raises
    ------
    TypeError
        If nothing matches *spec*.
    ValueError
        If the shorthand is malformed (a slider with ``min >= max``, no options).

    See Also
    --------
    controls : Declare the controls of a drawing function.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.widgets.control((0, 10))
    IntSlider(label=None, units=None, format=None, min=0, max=10, step=1, value=None)
    >>> type(svg.widgets.control(["♠", "♥", "♦", "♣"])).__name__, type(svg.widgets.control(list("ABCDE"))).__name__
    ('Segmented', 'Dropdown')
    >>> svg.widgets.control(svg.mm(5)).units
    'mm'
    """
    if isinstance(spec, Control):
        return spec.titled(label) if label else spec
    if isinstance(spec, bool):
        return Toggle(spec, label=label)
    if is_color(spec):
        return ColorPicker(spec, label=label)
    if isinstance(spec, str):
        return Text(spec, label=label)
    if _is_number(spec) or isinstance(spec, Length):
        return _around(spec, label)
    if isinstance(spec, tuple) and len(spec) in (2, 3) and all(_is_number(p) or isinstance(p, Length) for p in spec):
        return _slider(*spec, label=label)
    if isinstance(spec, Mapping) or isinstance(spec, Sequence) and not isinstance(spec, (str, bytes)):
        options = list(spec.values()) if isinstance(spec, Mapping) else list(spec)
        if options and all(is_color(option) for option in options):
            return Swatches(spec, label=label)
        kind = Segmented if len(options) <= SEGMENTED_MAX else Dropdown
        return kind(spec, label=label)
    raise TypeError(f"no control for {spec!r}; pass a Control such as svg.widgets.Slider(...)")


def _parameters(function: Callable[..., Any]) -> Mapping[str, inspect.Parameter]:
    try:
        return inspect.signature(function).parameters
    except (TypeError, ValueError):
        return {}


def accepts(function: Callable[..., Any], names: Sequence[str]) -> None:
    parameters = _parameters(function)
    if not parameters or any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters.values()):
        return
    unknown = [name for name in names if name not in parameters]
    if unknown:
        raise TypeError(f"{getattr(function, '__name__', function)!r} has no parameter {', '.join(unknown)}")


def controls(**specs: Any) -> Callable[[F], F]:
    """Declare the controls of a drawing function, by parameter name.

    :func:`~svgwriter.explore`, :func:`~svgwriter.sweep` and ``svgwriter preview`` read them, and
    ``svgwriter build`` calls the function with their starting values.

    Parameters
    ----------
    **specs : object
        A control or a shorthand (see :func:`control`) per parameter.

    Returns
    -------
    callable
        A decorator that returns the function unchanged, with the controls attached.

    Raises
    ------
    TypeError
        If a name is not a parameter of the function, or a shorthand matches no control.

    See Also
    --------
    controls_of : The controls a function ends up with.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.widgets.controls(radius=(0, 40), filled=False)
    ... def badge(doc, radius=12, filled=True):
    ...     doc.circle(50, 50, radius, fill="tomato" if filled else "none", stroke="black")
    >>> {name: c.initial for name, c in svg.widgets.controls_of(badge).items()}
    {'radius': 12, 'filled': False}
    """
    built = {name: control(spec) for name, spec in specs.items()}

    def attach(function: F) -> F:
        accepts(function, list(built))
        setattr(function, CONTROLS_ATTRIBUTE, {**getattr(function, CONTROLS_ATTRIBUTE, {}), **built})
        return function

    return attach


def controls_of(function: Callable[..., Any], *, infer: bool = True, **specs: Any) -> dict[str, Control]:
    """The controls of *function*: those declared with :func:`controls`, then *specs*, labelled by name.

    With neither, controls are inferred from the function's keyword defaults where a shorthand matches
    (``size=40`` gives a slider, ``glow=False`` a toggle). A control without a starting value starts at
    the function's default for that parameter.

    Parameters
    ----------
    function : callable
        The drawing function.
    infer : bool, optional
        Infer controls from keyword defaults when none are declared or given. Defaults to True.
    **specs : object
        Further controls or shorthands, overriding declared ones of the same name.

    Returns
    -------
    dict of str to Control
        One control per parameter, in declaration order.

    Raises
    ------
    TypeError
        If a name is not a parameter of the function.

    Examples
    --------
    >>> import svgwriter as svg
    >>> def ring(size=40, glow=False, label="Hi"):
    ...     return svg.circle(0, 0, size)
    >>> {name: type(c).__name__ for name, c in svg.widgets.controls_of(ring).items()}
    {'size': 'IntSlider', 'glow': 'Toggle', 'label': 'Text'}
    """
    accepts(function, list(specs))
    parameters = _parameters(function)
    chosen = {**getattr(function, CONTROLS_ATTRIBUTE, {}), **{name: control(s) for name, s in specs.items()}}
    if infer and not chosen:
        for name, parameter in parameters.items():
            if parameter.default is not inspect.Parameter.empty and parameter.default is not None:
                try:
                    chosen[name] = control(parameter.default)
                except (TypeError, ValueError):
                    continue
    resolved = {}
    for name, item in chosen.items():
        item = item.titled(name)
        default = parameters[name].default if name in parameters else inspect.Parameter.empty
        if getattr(item, "value", None) in (None, ()) and default not in (inspect.Parameter.empty, None):
            item = item.starting_at(default)
        resolved[name] = item
    return resolved
