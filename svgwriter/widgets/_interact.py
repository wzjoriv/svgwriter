"""
``svg.interact``: a drawing beside its controls, redrawn as they change.
"""

from __future__ import annotations

import threading
import traceback
from collections import OrderedDict
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol

from .._internal._typing import AnyPath
from ..document import Document
from ._constants import DEBOUNCE_SECONDS, RENDER_CACHE
from ._control import Control
from ._draw import arguments, draw
from ._infer import controls_of

__all__ = ["Backend", "Interactive", "interact"]

Changed = Callable[[str, Any], None]


class Backend(Protocol):
    """What shows an :class:`Interactive`: a panel of inputs, the drawing and the last error.

    The notebook backend uses ipywidgets; tests and other front ends supply their own.
    """

    def panel(self, controls: Mapping[str, Control], values: Mapping[str, Any], changed: Changed) -> None:
        """Build one input per control, starting at *values*; call ``changed(name, raw)`` on every edit."""

    def draw(self, svg: str) -> None:
        """Show the drawing, given as SVG markup."""

    def fail(self, message: str | None) -> None:
        """Show *message* under the drawing, or clear it when None."""

    def show(self) -> None:
        """Display the panel."""


def _frozen(value: Any) -> Any:
    return tuple(_frozen(part) for part in value) if isinstance(value, (list, tuple)) else value


def _cell() -> int | None:
    try:
        from IPython import get_ipython  # type: ignore[import-not-found]
    except ImportError:
        return None
    shell = get_ipython()
    return getattr(shell, "execution_count", None) if shell is not None else None


class Interactive:
    """A drawing function with live controls; :func:`interact` makes one.

    Parameters
    ----------
    function : callable
        Returns a :class:`~svgwriter.Document` or an element for keyword arguments named like the controls.
    controls : mapping of str to Control
        One control per parameter.
    backend : Backend
        What shows the panel.
    delay : float, optional
        Seconds to wait after the last change before redrawing. Defaults to 0.08; 0 redraws at once.

    Attributes
    ----------
    controls : dict of str to Control
        The controls, by parameter name.
    error : str or None
        The traceback of the last failed redraw, or None.

    See Also
    --------
    interact : Build and show one in a notebook.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.widgets import Interactive, Slider
    >>> class Quiet:
    ...     def panel(self, controls, values, changed): pass
    ...     def draw(self, svg): pass
    ...     def fail(self, message): pass
    ...     def show(self): pass
    >>> dot = Interactive(lambda r: svg.circle(10, 10, r), {"r": Slider(1, 10)}, Quiet(), delay=0)
    >>> dot.update(r=4).code()
    '<lambda>(r=4.0)'
    """

    def __init__(self, function: Callable[..., Any], controls: Mapping[str, Control], backend: Backend,
                 delay: float = DEBOUNCE_SECONDS) -> None:
        self.function = function
        self.controls = dict(controls)
        self.error: str | None = None
        self._backend, self._delay = backend, delay
        self._values = {name: control.initial for name, control in self.controls.items()}
        self._cache: OrderedDict[tuple[Any, ...], tuple[Document, str]] = OrderedDict()
        self._shown: tuple[Document, str] | None = None
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._cell = _cell()
        backend.panel(self.controls, dict(self._values), self._changed)
        self.redraw()

    def __repr__(self) -> str:
        return f"<Interactive {self.code()}>"

    @property
    def values(self) -> dict[str, Any]:
        """The current value of every control, by name.

        Returns
        -------
        dict
            A copy; change values with :meth:`update`.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.interact(lambda n=3: svg.text(str(n)), backend=svg.widgets.Recorder()).values
        {'n': 3}
        """
        return dict(self._values)

    @property
    def document(self) -> Document:
        """The drawing for the current values.

        Returns
        -------
        Document
            The last drawing made; after an error, the last one that worked.

        Raises
        ------
        RuntimeError
            If no drawing has worked yet.

        Examples
        --------
        >>> import svgwriter as svg
        >>> view = svg.interact(lambda r=5: svg.circle(r, r, r), backend=svg.widgets.Recorder())
        >>> view.document.root[0].tag
        'circle'
        """
        if self._shown is None:
            raise RuntimeError(f"no drawing yet: {self.error or 'nothing rendered'}")
        return self._shown[0]

    def update(self, **values: Any) -> Interactive:
        """Set controls by name and redraw at once.

        Parameters
        ----------
        **values : object
            New values, checked by their controls.

        Returns
        -------
        Interactive
            Itself, for chaining.

        Raises
        ------
        KeyError
            If a name is not a control.
        ValueError
            If a value fails its control's check.

        Examples
        --------
        >>> import svgwriter as svg
        >>> view = svg.interact(lambda r=5: svg.circle(r, r, r), backend=svg.widgets.Recorder())
        >>> view.update(r=8).values
        {'r': 8}
        """
        for name, value in values.items():
            if name not in self.controls:
                raise KeyError(f"no control {name!r}; the controls are {', '.join(self.controls)}")
            self._values[name] = self.controls[name].check(value)
        self.redraw()
        return self

    def redraw(self) -> None:
        """Draw the current values (from the cache when they were drawn before) and show the result.

        On an error the previous drawing stays and the traceback is shown under it.

        Examples
        --------
        >>> import svgwriter as svg
        >>> view = svg.interact(lambda r=5: svg.circle(r, r, r), backend=svg.widgets.Recorder())
        >>> view.redraw()
        """
        key = tuple((name, _frozen(value)) for name, value in self._values.items())
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                try:
                    document = draw(self.function, arguments(self.controls, self._values))
                    entry = (document, document._repr_svg_())
                except Exception:
                    self.error = traceback.format_exc()
                    self._backend.fail(self.error)
                    return
                self._cache[key] = entry
                if len(self._cache) > RENDER_CACHE:
                    self._cache.popitem(last=False)
            else:
                self._cache.move_to_end(key)
            self.error = None
            if entry is not self._shown:
                self._shown = entry
                self._backend.draw(entry[1])
            self._backend.fail(None)

    def _changed(self, name: str, raw: Any) -> None:
        try:
            self._values[name] = self.controls[name].from_form(raw)
        except (TypeError, ValueError) as error:
            self.error = f"{self.controls[name].label}: {error}"
            self._backend.fail(self.error)
            return
        if self._delay <= 0:
            self.redraw()
            return
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(self._delay, self.redraw)
        self._timer.daemon = True
        self._timer.start()

    def save(self, path: AnyPath, **options: Any) -> Path:
        """Save the drawing for the current values; the extension picks the format.

        Parameters
        ----------
        path : str or path-like
            The file to write (``.svg``, ``.png``, ``.pdf``, ...).
        **options : object
            Passed to :meth:`Document.save <svgwriter.Document.save>`.

        Returns
        -------
        pathlib.Path
            The written file.

        Examples
        --------
        >>> import svgwriter as svg
        >>> view = svg.interact(lambda r=5: svg.circle(r, r, r), backend=svg.widgets.Recorder())
        >>> view.save("dot.svg")  # doctest: +SKIP
        """
        target = Path(path)
        self.document.save(target, **options)
        return target

    def code(self) -> str:
        """The call that draws the current state, for copying into a script.

        Returns
        -------
        str
            ``name(param=value, ...)``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> def card(rank="A", glow=False):
        ...     return svg.text(rank)
        >>> svg.interact(card, backend=svg.widgets.Recorder()).update(glow=True).code()
        "card(rank='A', glow=True)"
        """
        parts = (f"{name}={self.controls[name].code(value)}" for name, value in self._values.items())
        return f"{getattr(self.function, '__name__', 'draw')}({', '.join(parts)})"

    def show(self) -> None:
        """Display the panel again (a notebook shows it once when :func:`interact` runs).

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.interact(lambda r=5: svg.circle(r, r, r), backend=svg.widgets.Recorder()).show()
        """
        self._backend.show()

    def _ipython_display_(self) -> None:
        if self._cell is not None and self._cell == _cell():
            return
        self.show()


def interact(function: Callable[..., Any], *, backend: Backend | None = None, delay: float = DEBOUNCE_SECONDS,
             **controls: Any) -> Interactive:
    """Show *function*'s drawing beside a panel of controls, redrawn as they change.

    The function returns a :class:`~svgwriter.Document` or an element; a function whose first parameter is
    not a control (a project's ``build(doc, ...)``) receives a new document there. Redraws wait for the
    controls to settle, repeated values come from a cache, and an error keeps the previous drawing with
    the traceback under it.

    Parameters
    ----------
    function : callable
        The drawing function.
    backend : Backend, optional
        What shows the panel. Defaults to None, ipywidgets in a notebook.
    delay : float, optional
        Seconds to wait after the last change before redrawing. Defaults to 0.08.
    **controls : object
        A :class:`Control` or a shorthand per parameter (see :func:`~svgwriter.widgets.control`),
        added to those declared with :func:`~svgwriter.widgets.controls`. With none at all, they are
        inferred from the function's keyword defaults.

    Returns
    -------
    Interactive
        ``.values``, ``.document``, ``.save(path)`` and ``.code()`` for the current state.

    Raises
    ------
    ImportError
        Without a backend when ipywidgets is not installed (``pip install pysvgwriter[widget]``).
    TypeError
        If a control names no parameter of *function*.

    See Also
    --------
    sweep : Step the same parameters over time instead.

    Examples
    --------
    >>> import svgwriter as svg
    >>> def badge(radius=12, color="#0ea5e9"):
    ...     return svg.circle(radius, radius, radius, fill=color)
    >>> view = svg.interact(badge, radius=(4, 40), color=["#0ea5e9", "#f43f5e"], backend=svg.widgets.Recorder())
    >>> view.update(radius=30).code()
    "badge(radius=30, color='#0ea5e9')"
    """
    if backend is None:
        from ._ipywidgets import NotebookBackend

        backend = NotebookBackend()
    view = Interactive(function, controls_of(function, **controls), backend, delay)
    view.show()
    return view
