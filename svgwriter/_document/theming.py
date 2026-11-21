"""
Document theme: the theme in use and the output preparation that applies it.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from ..theme.sheet import applied
from ..theme.theme import Theme


class Theming:
    """The document theme; mixed into :class:`~svgwriter.Document`."""

    @property
    def theme(self) -> Theme:
        """The theme that styles elements marked with ``as_role``; assign a theme or a registered name.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> doc.theme.name
        'light'
        >>> doc.theme = "dark"
        >>> doc.theme.name
        'dark'
        """
        return self._theme

    @theme.setter
    def theme(self, value: Theme | str) -> None:
        self._theme = Theme.of(value)

    @contextmanager
    def _prepared(self) -> Iterator[None]:
        with self._sized(), applied(self._theme, self.root):
            yield
