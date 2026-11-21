"""
Animation presets for every item of a batch, with per-item arguments and a stagger.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from ._batch import Batch

__all__ = ["BatchMotion"]


def _timing_name(preset: Callable[..., Any]) -> str | None:
    """The keyword a preset takes its start time by: ``begin``, ``at`` (show, hide) or none (behaviors)."""
    try:
        parameters = inspect.signature(preset).parameters
    except (TypeError, ValueError):
        return "begin"
    return next((name for name in ("begin", "at") if name in parameters), None)


class BatchMotion:
    """``batch.animate``: each preset runs on every item, each item starting *stagger* seconds after the last.

    Every preset of :attr:`Element.animate <svgwriter.model.elements.Element.animate>` is available
    with its own arguments plus ``stagger`` (seconds, default 0). Array arguments with one entry per
    item (``begin`` included) give each item its own value; anything else is shared.

    Parameters
    ----------
    batch : Batch
        The batch to animate; it is expanded.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> dots = svg.batch.circles([0, 10], 0, 2)
    >>> _ = dots.animate.move_to(np.array([5, 15]), 20, dur=1)
    >>> len(dots[0].children), len(dots[1].children)
    (1, 1)
    """

    __slots__ = ("batch",)

    def __init__(self, batch: Batch) -> None:
        self.batch = batch

    def __getattr__(self, name: str) -> Callable[..., BatchMotion]:
        if name.startswith("_"):
            raise AttributeError(name)
        preset = getattr(self.batch.items[0].animate if len(self.batch) else _probe().animate, name)
        timing = _timing_name(preset)

        def run(*args: Any, stagger: float = 0.0, **options: Any) -> BatchMotion:
            items = self.batch.items
            count = len(items)
            if timing is not None:
                start = np.broadcast_to(np.asarray(options.get(timing, 0.0), dtype=float), (count,))
                options[timing] = start + stagger * np.arange(count)
            for index, item in enumerate(items):
                getattr(item.animate, name)(*(_pick(value, index, count) for value in args),
                                            **{key: _pick(value, index, count) for key, value in options.items()})
            return self

        run.__name__ = name
        run.__doc__ = preset.__doc__
        return run

    def __dir__(self) -> list[str]:
        return sorted(set(dir(_probe().animate)) - {"element"})


def _probe() -> Any:
    from ..elements.shapes import Circle

    return Circle(0, 0, 1)


def _pick(value: Any, index: int, count: int) -> Any:
    """Item *index*'s share of *value*: its entry of a one-per-item array, else *value* itself."""
    if isinstance(value, np.ndarray) and value.ndim >= 1 and value.shape[0] == count:
        entry = value[index]
        return entry.item() if isinstance(entry, np.generic) else entry
    return value
