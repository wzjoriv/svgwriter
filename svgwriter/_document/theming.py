"""
Document theme: the theme in use and the output preparation that applies it.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from ..model.attributes.rules import set_class_rules
from ..model.layout import settle
from ..model.theme.sheet import applied, role_rules
from ..model.theme.theme import Theme


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
        set_class_rules(self.root, role_rules(self._theme))  # type: ignore[attr-defined]

    @contextmanager
    def _prepared(self) -> Generator[None, None, None]:
        with applied(self._theme, self.root):
            settle(self.root)
            with self._sized():
                yield
