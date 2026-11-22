"""
Name registries (built-in and user entries, plugins from entry points) and method decorators.
"""

from __future__ import annotations

import builtins
import difflib
import functools
import warnings
from collections.abc import Callable, Iterator
from typing import Concatenate, Generic, TypeVar, overload

from ._constants import ENTRY_POINT_PREFIX, SUGGESTIONS
from ._errors import UnknownNameError
from ._typing import P

__all__ = ["Registry", "chainable", "owner_of"]

T = TypeVar("T")
S = TypeVar("S")



def owner_of(item: object) -> str:
    """Where *item* is defined, as ``module.qualname``, or what it is for an instance."""
    qualname = getattr(item, "__qualname__", None)
    if qualname is None:
        return f"a {type(item).__name__} ({item!r})"
    return f"{getattr(item, '__module__', None) or '?'}.{qualname}"


class Registry(Generic[T]):
    """Entries of one kind by name: built-in ones, and user ones that add to or replace them.

    Every registry works the same way: :meth:`register` as a decorator (bare or with ``name=`` and
    ``replace=``) or a call, :meth:`list`, :meth:`get` and :meth:`unregister`. A taken name raises an error
    naming its owner, an unknown one an :class:`UnknownNameError` with the closest names. Packages add
    entries through the ``svgwriter.<kind>`` entry-point group (see :attr:`group`), loaded the first time a
    name is not found or the registry is listed.

    Parameters
    ----------
    kind : str
        What the entries are, for messages and the entry-point group (``"theme"``).
    builtins : callable, optional
        Imports the built-in entries; called once, before the first lookup or registration. Defaults to
        None, for registries filled at import time.
    group : str, optional
        The entry-point group plugins register into. Defaults to None, which is ``"svgwriter.<kind>"``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> "dark" in svg.themes.list(), svg.themes.group
    (True, 'svgwriter.theme')
    """

    def __init__(self, kind: str, builtins: Callable[[], object] | None = None, *, group: str | None = None) -> None:
        self.kind = kind
        self.group = group or ENTRY_POINT_PREFIX + kind
        self.builtins: dict[str, T] = {}
        self.user: dict[str, T] = {}
        self._load_builtins = builtins
        self._plugins_loaded = False

    @overload
    def register(self, item: T, /, *, name: str | None = None, replace: bool = False) -> T: ...

    @overload
    def register(self, *, name: str | None = None, replace: bool = False) -> Callable[[T], T]: ...

    def register(self, item: T | None = None, /, *, name: str | None = None,
                 replace: bool = False) -> T | Callable[[T], T]:
        """Register *item*, or return a decorator that does.

        Parameters
        ----------
        item : object, optional
            The entry. Given when used as a bare decorator or a call.
        name : str, optional
            The name. Defaults to None, which takes the item's ``__name__`` (functions and classes) or
            ``name`` (themes, presets).
        replace : bool, optional
            Replace an entry already registered under the name, a built-in one included. Defaults to False.

        Returns
        -------
        object
            The registered entry, or a decorator that registers and returns it.

        Raises
        ------
        ValueError
            If the name is taken and `replace` is False; the message names the owner.
        """

        def decorate(entry: T) -> T:
            label = name or self.name_of(entry)
            return self.add(label, self.prepare(label, entry), replace=replace)

        return decorate if item is None else decorate(item)

    __call__ = register

    def name_of(self, item: object) -> str:
        """The name *item* registers under when none is given."""
        label = getattr(item, "__name__", None) or getattr(item, "name", None)
        if not isinstance(label, str):
            raise TypeError(f"{self.kind} {item!r} has no name; pass name=")
        return label

    def prepare(self, name: str, item: T) -> T:
        """Check *item* and return what is stored under *name* (the item itself unless a kind wraps it)."""
        return item

    def add(self, name: str, item: T, *, replace: bool = False) -> T:
        """Store *item* under *name*; a taken name raises ValueError naming its owner unless *replace*."""
        self._builtins()
        current = self.user.get(name, self.builtins.get(name))
        if current is not None and not replace:
            built_in = " (built in)" if name in self.builtins and name not in self.user else ""
            raise ValueError(f"{self.kind} {name!r} is already registered by {owner_of(current)}{built_in}; "
                             "pass replace=True to replace it")
        self.user[name] = item
        return item

    def add_builtin(self, name: str, item: T) -> T:
        """Store a built-in entry."""
        self.builtins[name] = item
        return item

    def seal(self) -> None:
        """Make every entry registered so far a built-in one (called once the built-ins are imported)."""
        self.builtins.update(self.user)
        self.user.clear()

    def unregister(self, name: str) -> T:
        """Remove the entry registered as *name* and return it; a replaced built-in comes back.

        Parameters
        ----------
        name : str
            The registered name.

        Returns
        -------
        object
            The removed entry.

        Raises
        ------
        UnknownNameError
            If nothing is registered under *name*, or it is built in (built-ins are replaced, not removed).
        """
        self._builtins()
        if name not in self.user:
            if name in self.builtins:
                raise UnknownNameError(f"{self.kind} {name!r} is built in; replace it with replace=True instead")
            raise UnknownNameError(self.unknown(name))
        return self.user.pop(name)

    def get(self, name: str) -> T:
        """The entry registered as *name*: the user's if one replaced it, else the built-in.

        Parameters
        ----------
        name : str
            The registered name.

        Returns
        -------
        object
            The entry.

        Raises
        ------
        UnknownNameError
            If nothing has that name; the message suggests the closest names.
        """
        found = self.find(name)
        if found is None:
            raise UnknownNameError(self.unknown(name))
        return found

    def find(self, name: str, *, plugins: bool = True) -> T | None:
        """The entry registered as *name*, or None; *plugins* loads the entry points on a miss."""
        self._builtins()
        for attempt in range(2):
            if name in self.user:
                return self.user[name]
            if name in self.builtins:
                return self.builtins[name]
            if attempt or not plugins or not self._plugins():
                return None
        return None

    def list(self) -> builtins.list[str]:
        """Every registered name: built-in ones first, then the ones registered since.

        Returns
        -------
        list of str
            The names.
        """
        return self._names(plugins=True)

    def _names(self, *, plugins: bool) -> builtins.list[str]:
        """Every name, loading the entry points first when *plugins* is True."""
        self._builtins()
        if plugins:
            self._plugins()
        return [*self.builtins, *(name for name in self.user if name not in self.builtins)]

    def unknown(self, name: str) -> str:
        """The message for an unknown *name*, with the closest names."""
        close = difflib.get_close_matches(name, self.list(), n=SUGGESTIONS)
        hint = f"; did you mean {' or '.join(map(repr, close))}?" if close else ""
        return f"unknown {self.kind} {name!r}{hint}"

    def state(self) -> dict[str, T]:
        """A copy of the user entries, for :meth:`restore`."""
        return dict(self.user)

    def restore(self, state: dict[str, T]) -> None:
        self.user = dict(state)

    def _builtins(self) -> None:
        load, self._load_builtins = self._load_builtins, None
        if load is not None:
            load()
            self.seal()

    def _plugins(self) -> bool:
        """Load the entry points of :attr:`group` once; whether this call loaded them."""
        if self._plugins_loaded:
            return False
        self._plugins_loaded = True
        from importlib.metadata import entry_points

        for point in entry_points(group=self.group):
            before = len(self.user)
            try:
                loaded = point.load()
                if len(self.user) == before and point.name not in self.user:
                    self.register(loaded, name=point.name)
            except Exception as error:
                warnings.warn(f"{self.kind} plugin {point.name!r} ({point.value}) failed to load: {error}",
                              RuntimeWarning, stacklevel=3)
        return True

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.find(name) is not None

    def __iter__(self) -> Iterator[str]:
        return iter(self.list())

    def __len__(self) -> int:
        return len(self.list())

    def __repr__(self) -> str:
        return f"<{self.kind} registry: {', '.join(self.list())}>"


def chainable(method: Callable[Concatenate[S, P], object]) -> Callable[Concatenate[S, P], S]:
    """Make *method* return ``self`` so calls can be chained."""

    @functools.wraps(method)
    def wrapper(self: S, /, *args: P.args, **kwargs: P.kwargs) -> S:
        method(self, *args, **kwargs)
        return self

    return wrapper

