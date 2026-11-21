"""
``Fonts``: the font families, sizes and weights of a theme.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ._constants import FONT_FAMILY, FONT_SIZES, FONT_WEIGHTS, MONOSPACE_FAMILY
from ._errors import ThemeError

__all__ = ["Fonts"]


@dataclass(frozen=True)
class Fonts:
    """Font families, named sizes (user units) and named weights.

    Parameters
    ----------
    family : str, optional
        CSS ``font-family`` of ordinary text. Defaults to a sans-serif stack.
    monospace : str, optional
        CSS ``font-family`` of code. Defaults to a monospace stack.
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

    family: str = FONT_FAMILY
    monospace: str = MONOSPACE_FAMILY
    sizes: Mapping[str, float] = field(default_factory=lambda: dict(FONT_SIZES))
    weights: Mapping[str, int] = field(default_factory=lambda: dict(FONT_WEIGHTS))

    def __post_init__(self) -> None:
        object.__setattr__(self, "sizes", MappingProxyType(dict(self.sizes)))
        object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))

    def replace(self, *, family: str | None = None, monospace: str | None = None,
                sizes: Mapping[str, float] | None = None, weights: Mapping[str, int] | None = None) -> Fonts:
        """A copy with some values replaced; ``sizes`` and ``weights`` merge by name.

        Parameters
        ----------
        family, monospace : str, optional
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
            ``family``, ``monospace``, ``sizes`` and ``weights``.

        Examples
        --------
        >>> from svgwriter.theme import Fonts
        >>> sorted(Fonts().to_dict())
        ['family', 'monospace', 'sizes', 'weights']
        """
        return {"family": self.family, "monospace": self.monospace,
                "sizes": dict(self.sizes), "weights": dict(self.weights)}
