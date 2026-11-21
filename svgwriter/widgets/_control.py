"""
The base of every control: a label, a starting value, validation and how a value is shown and written as code.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, TypeVar

__all__ = ["Control"]

C = TypeVar("C", bound="Control")


@dataclass(frozen=True, kw_only=True)
class Control:
    """One adjustable parameter: pure data, read the same way by notebooks, ``svgwriter preview`` and sweeps.

    Subclasses add their own ``value`` and checks; a control does not hold the current value of a panel, only
    its starting value.

    Parameters
    ----------
    label : str, optional
        Shown beside the input. Defaults to None, the parameter name with underscores as spaces.

    See Also
    --------
    svgwriter.widgets.control : Build a control from shorthand such as ``(0, 10)``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> radius = svg.widgets.Slider(0, 20, label="corner radius")
    >>> radius.initial, radius.check(4)
    (10.0, 4.0)
    """

    label: str | None = None

    @property
    def initial(self) -> Any:
        """The starting value: ``value`` when given, else a natural default (a slider's middle, the first option).

        Returns
        -------
        object
            A value that passes :meth:`check`.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.widgets.Segmented(["a", "b"]).initial
        'a'
        """
        value = getattr(self, "value", None)
        return self.check(value) if value is not None else self._default()

    def _default(self) -> Any:
        raise NotImplementedError

    def check(self, value: Any) -> Any:
        """Validate *value* and return it in the control's own form (a float, a hex colour, an option).

        Parameters
        ----------
        value : object
            A candidate value.

        Returns
        -------
        object
            The normalized value.

        Raises
        ------
        ValueError
            If the value is out of range or not an option.
        TypeError
            If the value has the wrong type.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.widgets.Toggle().check(True)
        True
        """
        raise NotImplementedError

    def from_form(self, raw: Any) -> Any:
        """The value a form field sends: options arrive as indices, everything else as the value itself.

        Parameters
        ----------
        raw : object
            What the input produced (a JSON value).

        Returns
        -------
        object
            The checked value.

        Raises
        ------
        ValueError
            If the value is invalid.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.widgets.Dropdown(["low", "high"]).from_form(1)
        'high'
        """
        return self.check(raw)

    def argument(self, value: Any) -> Any:
        """What the drawing function receives for *value* (a :class:`~svgwriter.Length` for sliders in a unit).

        Parameters
        ----------
        value : object
            A checked value.

        Returns
        -------
        object
            The argument.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.widgets.Slider(0, 10, units="mm").argument(4.0))
        '4mm'
        """
        return value

    def code(self, value: Any) -> str:
        """*value* as Python source, for :meth:`Interactive.code <svgwriter.widgets.Interactive.code>`.

        Parameters
        ----------
        value : object
            A checked value.

        Returns
        -------
        str
            A Python expression.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.widgets.Text("Hi").code("Hi")
        "'Hi'"
        """
        return repr(value)

    def text(self, value: Any) -> str:
        """*value* as a short readout for the panel.

        Parameters
        ----------
        value : object
            A checked value.

        Returns
        -------
        str
            The readout.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.widgets.Slider(0, 1, format=".0%").text(0.25)
        '25%'
        """
        return str(value)

    def titled(self: C, name: str) -> C:
        """This control with a label derived from *name* when it has none.

        Parameters
        ----------
        name : str
            The parameter name.

        Returns
        -------
        Control
            A copy with a label.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.widgets.Toggle().titled("show_grid").label
        'show grid'
        """
        return self if self.label else dataclasses.replace(self, label=name.replace("_", " "))

    def starting_at(self: C, value: Any) -> C:
        """This control starting at *value* instead.

        Parameters
        ----------
        value : object
            The new starting value.

        Returns
        -------
        Control
            A copy.

        Raises
        ------
        ValueError
            If *value* does not pass :meth:`check`.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.widgets.Slider(0, 10).starting_at(3).initial
        3.0
        """
        return dataclasses.replace(self, value=self.check(value))  # type: ignore[call-arg]
