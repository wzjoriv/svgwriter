"""
Theme files: ``Theme.load``, ``save``, ``from_toml`` and ``to_toml``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from .._internal._typing import AnyPath
from ._errors import ThemeError
from ._toml_read import theme_from_toml
from ._toml_write import theme_to_toml

if TYPE_CHECKING:
    from .theme import Theme

__all__ = ["ThemeFiles"]


class ThemeFiles:
    """Reading and writing TOML theme files; mixed into :class:`~svgwriter.Theme`."""

    __slots__ = ()

    @classmethod
    def load(cls, path: AnyPath) -> Theme:
        """Read a TOML theme file (see :meth:`from_toml`).

        Parameters
        ----------
        path : str or os.PathLike
            The file.

        Returns
        -------
        Theme
            The theme. It remembers the file's text, so :meth:`save` keeps its comments and layout.

        Raises
        ------
        ThemeError
            If the file is not a valid theme; the message starts with the file's path.

        Examples
        --------
        >>> import svgwriter as svg, tempfile, pathlib
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "night.toml"
        ...     svg.Theme.get("dark").replace(name="night").save(path)
        ...     svg.Theme.load(path).name
        'night'
        """
        path = Path(os.fspath(path))
        try:
            return cls.from_toml(path.read_text(encoding="utf-8"))
        except ThemeError as error:
            raise ThemeError(f"{path}: {error}") from None

    def save(self, path: AnyPath) -> None:
        """Write the theme as TOML (see :meth:`to_toml`).

        Parameters
        ----------
        path : str or os.PathLike
            The file to write.

        Examples
        --------
        >>> import svgwriter as svg, tempfile, pathlib
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "night.toml"
        ...     svg.Theme.get("dark").replace(name="night").save(path)
        ...     print(path.read_text(encoding="utf-8"))
        name = "night"
        extends = "dark"
        <BLANKLINE>
        """
        Path(os.fspath(path)).write_text(self.to_toml(), encoding="utf-8")

    @classmethod
    def from_toml(cls, text: str) -> Theme:
        """Build a theme from TOML text.

        The file is a variant of ``extends`` (a registered name, default ``"light"``) with
        ``name``, ``[palette]``, ``[fonts]`` (with ``[fonts.sizes]`` and ``[fonts.weights]``) and
        ``[roles.<name>]`` tables. Values are text, numbers, color arrays (``[r, g, b]`` or
        ``[r, g, b, a]``: all floats from 0 to 1 or all integers from 0 to 255), ``{palette.name}``
        / ``{fonts.sizes.name}`` references and expressions; nothing in the file runs Python.

        Parameters
        ----------
        text : str
            The TOML document.

        Returns
        -------
        Theme
            The theme. It remembers *text*, so :meth:`to_toml` keeps its comments and layout.

        Raises
        ------
        ThemeError
            On invalid TOML, unknown keys, unsupported values, unknown references or cycles.

        Examples
        --------
        >>> import svgwriter as svg
        >>> theme = svg.Theme.from_toml('''
        ... name = "night"
        ... extends = "dark"
        ... [palette]
        ... primary = "#ff8800"
        ... accent = "{palette.primary}"
        ... [roles.badge]
        ... fill = "{palette.accent}"
        ... ''')
        >>> theme.style("badge")["fill"].hex
        '#ff8800'
        """
        return theme_from_toml(text)

    def to_toml(self) -> str:
        """The theme as TOML: what differs from the theme it extends.

        Returns
        -------
        str
            The TOML document; :meth:`from_toml` reads it back to an equal theme.

        Raises
        ------
        ThemeError
            If the theme it extends is no longer registered.

        Notes
        -----
        Text values are written as given, so references and expressions stay live. Values given
        as Python functions are written as what they resolve to. A theme read from a file is
        written into that file's text: unchanged entries, comments and layout stay as they were,
        and only edited or new keys change. :meth:`~svgwriter.Theme.replace` on a registered theme
        records it as ``extends``; a theme built directly with ``Theme(...)`` is written in full,
        over ``light``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> text = '''# brand colours
        ... extends = "paper"
        ...
        ... [palette]
        ... primary = "#7c3aed"   # violet
        ... '''
        >>> theme = svg.Theme.from_toml(text).replace(palette={"accent": "{palette.primary}"})
        >>> print(theme.to_toml())
        # brand colours
        extends = "paper"
        <BLANKLINE>
        [palette]
        primary = "#7c3aed"   # violet
        accent = "{palette.primary}"
        <BLANKLINE>
        """
        return theme_to_toml(self)  # type: ignore[arg-type]
