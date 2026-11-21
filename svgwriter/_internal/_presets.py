"""
Preset registries: one per kind (animation, behavior, shape), with built-in entries that users may replace on purpose.
"""

from __future__ import annotations

import difflib
from collections.abc import Callable, Iterator
from typing import Any, Final

from ._constants import SUGGESTIONS

__all__ = ["ANIMATIONS", "BEHAVIORS", "KINDS", "SHAPES", "PresetRegistry", "owner_of"]

Preset = Callable[..., Any]


def owner_of(item: object) -> str:
    """Where *item* is defined, as ``module.qualname``."""
    module = getattr(item, "__module__", None) or "?"
    return f"{module}.{getattr(item, '__qualname__', type(item).__name__)}"


class PresetRegistry:
    """Presets of one kind by name: built-in ones, and user ones that add to or replace them."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.builtins: dict[str, Preset] = {}
        self.user: dict[str, Preset] = {}

    def add_builtin(self, name: str, item: Preset) -> Preset:
        self.builtins[name] = item
        return item

    def seal(self) -> None:
        """Make every preset registered so far a built-in one (called once the built-ins are imported)."""
        self.builtins.update(self.user)
        self.user.clear()

    def add(self, name: str, item: Preset, *, replace: bool = False) -> Preset:
        """Register *item*; a taken name raises ValueError naming its owner unless *replace* is True."""
        current = self.user.get(name, self.builtins.get(name))
        if current is not None and not replace:
            built_in = " (built in)" if name in self.builtins and name not in self.user else ""
            raise ValueError(f"{self.kind} {name!r} is already registered by {owner_of(current)}{built_in}; "
                             "pass replace=True to replace it")
        self.user[name] = item
        return item

    def remove(self, name: str) -> Preset:
        """Unregister a user preset; a replaced built-in comes back."""
        if name not in self.user:
            if name in self.builtins:
                raise KeyError(f"{self.kind} {name!r} is built in; replace it with replace=True instead")
            raise KeyError(self.unknown(name))
        return self.user.pop(name)

    def get(self, name: str) -> Preset:
        """The preset registered as *name*: the user's, else the built-in."""
        try:
            return self.user[name] if name in self.user else self.builtins[name]
        except KeyError:
            raise KeyError(self.unknown(name)) from None

    def unknown(self, name: str) -> str:
        """The message for an unknown *name*, with the closest names."""
        close = difflib.get_close_matches(name, self.names(), n=SUGGESTIONS)
        hint = f"; did you mean {' or '.join(map(repr, close))}?" if close else ""
        return f"unknown {self.kind} {name!r}{hint}"

    def names(self) -> list[str]:
        return [*self.builtins, *(name for name in self.user if name not in self.builtins)]

    def state(self) -> dict[str, Preset]:
        """A copy of the user entries, for :meth:`restore`."""
        return dict(self.user)

    def restore(self, state: dict[str, Preset]) -> None:
        self.user = dict(state)

    def __contains__(self, name: object) -> bool:
        return name in self.user or name in self.builtins

    def __iter__(self) -> Iterator[str]:
        return iter(self.names())

    def __len__(self) -> int:
        return len(self.names())


ANIMATIONS: Final = PresetRegistry("animation")
BEHAVIORS: Final = PresetRegistry("behavior")
SHAPES: Final = PresetRegistry("shape")
KINDS: Final = {"animation": ANIMATIONS, "behavior": BEHAVIORS, "shape": SHAPES}
