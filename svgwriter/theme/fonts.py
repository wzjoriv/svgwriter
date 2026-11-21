"""
``Fonts``: the font families, sizes and weights of a theme.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Union

from ._constants import FONT_FAMILY, FONT_SIZES, FONT_WEIGHTS, MONOSPACE_FAMILY
from ._errors import ThemeError

if TYPE_CHECKING:
    from ..ops.typeface import Typeface

__all__ = ["Family", "Fonts"]

Family = Union[str, "Typeface"]
"""A CSS ``font-family`` list or a :class:`~svgwriter.Typeface`."""


def family_data(value: Family) -> str | list[str]:
    """A family as theme files write it: the name, or the font files of a typeface loaded from files."""
    from ..ops.typeface import Typeface

    if not isinstance(value, Typeface):
        return value
    sources = [face.source for face in value.faces]
    if value.installed or None in sources:
        return value.name
    return [str(source) for source in sources]


@dataclass(frozen=True)
class Fonts:
    """Font families, named sizes (user units) and named weights.

    Parameters
    ----------
    family : str or Typeface, optional
        CSS ``font-family`` of ordinary text, or a :class:`~svgwriter.Typeface`
        (registered for rendering, embeddable with ``Document.embed_fonts``).
        Defaults to a sans-serif stack.
    monospace : str or Typeface, optional
        CSS ``font-family`` of code, or a typeface. Defaults to a monospace stack.
    sizes : mapping of str to float, optional
        Named font sizes such as ``"text"`` and ``"title"``. Defaults to text 14, title 24,
        subtitle 18 and caption 11.
    weights : mapping of str to int, optional
        Named weights such as ``"regular"`` and ``"bold"``. Defaults to 400 and 700.

    See Also
    --------
    Theme : Uses these values in its text roles.

    Examples
    --------
    >>> from svgwriter.theme import Fonts
    >>> fonts = Fonts().replace(sizes={"title": 30})
    >>> fonts.sizes["title"], fonts.sizes["text"]
    (30, 14.0)
    >>> fonts.lookup("weights.bold")
    700
    """

    family: Family = FONT_FAMILY
    monospace: Family = MONOSPACE_FAMILY
    sizes: Mapping[str, float] = field(default_factory=lambda: dict(FONT_SIZES))
    weights: Mapping[str, int] = field(default_factory=lambda: dict(FONT_WEIGHTS))

    def __post_init__(self) -> None:
        object.__setattr__(self, "sizes", MappingProxyType(dict(self.sizes)))
        object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))

    def replace(self, *, family: Family | None = None, monospace: Family | None = None,
                sizes: Mapping[str, float] | None = None, weights: Mapping[str, int] | None = None) -> Fonts:
        """A copy with some values replaced; ``sizes`` and ``weights`` merge by name.

        Parameters
        ----------
        family, monospace : str or Typeface, optional
            New families. Defaults to None, which keeps the current ones.
        sizes, weights : mapping, optional
            Entries to replace or add. Defaults to None.

        Returns
        -------
        Fonts
            The merged fonts.

        Examples
        --------
        >>> from svgwriter.theme import Fonts
        >>> Fonts().replace(family="Georgia, serif").family
        'Georgia, serif'
        """
        return Fonts(family if family is not None else self.family,
                     monospace if monospace is not None else self.monospace,
                     {**self.sizes, **(sizes or {})}, {**self.weights, **(weights or {})})

    def lookup(self, path: str) -> str | float | int:
        """The value at a dotted path: ``family``, ``monospace``, ``sizes.<name>`` or ``weights.<name>``.

        Parameters
        ----------
        path : str
            The path below ``fonts``.

        Returns
        -------
        str or float or int
            The value.

        Raises
        ------
        ThemeError
            If the path names nothing.

        Examples
        --------
        >>> from svgwriter.theme import Fonts
        >>> Fonts().lookup("sizes.caption")
        11.0
        """
        head, _, key = path.partition(".")
        if head in ("family", "monospace") and not key:
            return str(getattr(self, head))
        table = {"sizes": self.sizes, "weights": self.weights}.get(head)
        if table is None or key not in table:
            raise ThemeError(f"unknown font value fonts.{path}")
        return table[key]

    def to_dict(self) -> dict[str, object]:
        """The fonts as plain data, as written to theme files.

        Returns
        -------
        dict
            ``family``, ``monospace``, ``sizes`` and ``weights``; a typeface loaded
            from files is written as the list of its files.

        Examples
        --------
        >>> from svgwriter.theme import Fonts
        >>> sorted(Fonts().to_dict())
        ['family', 'monospace', 'sizes', 'weights']
        """
        return {"family": family_data(self.family), "monospace": family_data(self.monospace),
                "sizes": dict(self.sizes), "weights": dict(self.weights)}
