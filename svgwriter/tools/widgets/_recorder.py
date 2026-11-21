"""
``Recorder``: a backend that keeps what it is asked to show, for tests and scripts without a notebook.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._control import Control
from ._interact import Changed

__all__ = ["Recorder"]


class Recorder:
    """A :class:`Backend` that shows nothing and remembers everything; :meth:`set` plays a user's edit.

    Attributes
    ----------
    controls : dict of str to Control
        The controls of the panel.
    inputs : dict
        The value each input holds, as a form would send it.
    drawings : list of str
        Every SVG drawn, in order.
    message : str or None
        The error shown, or None.
    shown : int
        How many times the panel was displayed.

    See Also
    --------
    svgwriter.tools.widgets.interact : Takes ``backend=Recorder()``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> panel = svg.widgets.Recorder()
    >>> view = svg.interact(lambda size=10: svg.rect(0, 0, size, size), backend=panel, delay=0)
    >>> panel.set("size", 15)
    >>> view.values, len(panel.drawings)
    ({'size': 15}, 2)
    """

    def __init__(self) -> None:
        self.controls: dict[str, Control] = {}
        self.inputs: dict[str, Any] = {}
        self.drawings: list[str] = []
        self.message: str | None = None
        self.shown = 0
        self._changed: Changed | None = None

    def panel(self, controls: Mapping[str, Control], values: Mapping[str, Any], changed: Changed) -> None:
        self.controls, self.inputs, self._changed = dict(controls), dict(values), changed

    def draw(self, svg: str) -> None:
        self.drawings.append(svg)

    def fail(self, message: str | None) -> None:
        self.message = message

    def show(self) -> None:
        self.shown += 1

    def set(self, name: str, raw: Any) -> None:
        """Change input *name* to *raw*, as a person would (option controls take an index).

        Parameters
        ----------
        name : str
            The control.
        raw : object
            What the input sends.

        Raises
        ------
        RuntimeError
            If no panel was built.

        Examples
        --------
        >>> import svgwriter as svg
        >>> panel = svg.widgets.Recorder()
        >>> view = svg.interact(lambda suit="♠": svg.text(suit), suit=["♠", "♥"], backend=panel, delay=0)
        >>> panel.set("suit", 1)
        >>> view.values
        {'suit': '♥'}
        """
        if self._changed is None:
            raise RuntimeError("no panel yet")
        self.inputs[name] = raw
        self._changed(name, raw)
