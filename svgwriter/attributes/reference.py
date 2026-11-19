"""IRI references: ``#id`` and ``url(#id)``."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from .._internal._constants import DEFAULT_PRECISION

if TYPE_CHECKING:
    from ..elements.base import Element

__all__ = ["IRI", "FuncIRI", "parse_func_iri"]

_FUNC_IRI_RE: Final = re.compile(r"""^\s*url\(\s*(['"]?)(.*?)\1\s*\)\s*$""")


@dataclass(frozen=True)
class IRI:
    """A plain IRI, local (``#id``) or external.

    ``element`` is the referenced element when the IRI was made from one; it
    lets documents put unplaced definitions into ``<defs>`` automatically.

    Parameters
    ----------
    target : str
        The reference text, such as ``"#grad"`` or ``"image.svg#icon"``.
    element : Element, optional
        The referenced element, if known; ignored when comparing. Defaults to None.

    See Also
    --------
    FuncIRI : The ``url(...)`` form.

    Examples
    --------
    >>> from svgwriter.attributes import IRI
    >>> str(IRI.local("grad"))
    '#grad'
    """

    target: str
    element: Element | None = field(default=None, compare=False, repr=False)

    @classmethod
    def local(cls, element_id: str) -> IRI:
        """Return a reference to an element of the same document.

        Parameters
        ----------
        element_id : str
            The target's ``id``, without ``#``.

        Returns
        -------
        IRI
            An IRI of the form ``#id``.

        Examples
        --------
        >>> from svgwriter.attributes import IRI
        >>> IRI.local("a").target
        '#a'
        """
        return cls("#" + element_id)

    @property
    def fragment(self) -> str | None:
        """The part after ``#``, or ``None`` when there is no fragment.

        Examples
        --------
        >>> from svgwriter.attributes import IRI
        >>> IRI("image.svg#icon").fragment
        'icon'
        >>> IRI("image.svg").fragment is None
        True
        """
        _, sep, fragment = self.target.partition("#")
        return fragment if sep else None

    @property
    def current(self) -> str:
        """The target text, following the referenced element's id when it has changed since.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dot = svg.circle(0, 0, 1, id="a")
        >>> ref = dot.iri
        >>> dot.id = "b"
        >>> ref.current
        '#b'
        """
        element = self.element
        if element is not None and element.id is not None and self.target.startswith("#"):
            return "#" + element.id
        return self.target

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize the reference as attribute text.

        Parameters
        ----------
        precision : int, optional
            Unused; accepted for a uniform interface. Defaults to the library default precision.

        Returns
        -------
        str
            The IRI text.

        Examples
        --------
        >>> from svgwriter.attributes import IRI
        >>> IRI.local("a").svg_value()
        '#a'
        """
        return self.current

    def __str__(self) -> str:
        return self.svg_value()


@dataclass(frozen=True)
class FuncIRI(IRI):
    """A functional IRI, ``url(...)``, as used by paint and filter.

    Takes the same parameters as `IRI`.

    See Also
    --------
    parse_func_iri : Parse ``url(...)`` text.

    Examples
    --------
    >>> from svgwriter.attributes import FuncIRI
    >>> str(FuncIRI("#grad"))
    'url(#grad)'
    """

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize the reference as ``url(...)`` text.

        Parameters
        ----------
        precision : int, optional
            Unused; accepted for a uniform interface. Defaults to the library default precision.

        Returns
        -------
        str
            The IRI wrapped in ``url()``.
        """
        return f"url({self.current})"


def parse_func_iri(text: str) -> FuncIRI | None:
    """Parse ``url(...)`` text into a `FuncIRI`.

    Parameters
    ----------
    text : str
        Text such as ``"url(#grad)"``; quotes inside the parentheses are removed.

    Returns
    -------
    FuncIRI or None
        The reference, or ``None`` when the text is not a ``url(...)`` value.

    Examples
    --------
    >>> from svgwriter.attributes import parse_func_iri
    >>> parse_func_iri("url(#a)")
    FuncIRI(target='#a')
    >>> parse_func_iri("red") is None
    True
    """
    match = _FUNC_IRI_RE.match(text)
    return FuncIRI(match.group(2)) if match else None
