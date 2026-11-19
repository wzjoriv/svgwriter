"""The ``<paint>`` type used by ``fill`` and ``stroke``."""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias, Union

from .._internal._constants import DEFAULT_PRECISION
from ..attributes.reference import FuncIRI, parse_func_iri
from .color import Color, parse_color

if TYPE_CHECKING:
    from ..elements.base import Element

__all__ = ["Paint", "PaintKeyword", "PaintRef", "PaintValue", "parse_paint"]


class PaintKeyword(str, enum.Enum):
    """The paint keywords that are not colors.

    Members compare equal to their SVG text.

    Examples
    --------
    >>> from svgwriter.color import PaintKeyword
    >>> PaintKeyword.CURRENT_COLOR.value
    'currentColor'
    >>> PaintKeyword("none") is PaintKeyword.NONE
    True
    >>> str(PaintKeyword.CURRENT_COLOR)
    'currentColor'
    """

    NONE = "none"
    CURRENT_COLOR = "currentColor"
    INHERIT = "inherit"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PaintRef:
    """A paint server reference with an optional fallback.

    Parameters
    ----------
    iri : FuncIRI
        The ``url(#id)`` reference to a gradient or pattern.
    fallback : Color or PaintKeyword, optional
        Paint used when the reference cannot be resolved. Defaults to None.

    See Also
    --------
    parse_paint : Parse ``fill`` or ``stroke`` text.

    Examples
    --------
    >>> from svgwriter.color import PaintRef, parse_color
    >>> from svgwriter.attributes.reference import FuncIRI
    >>> str(PaintRef(FuncIRI("#grad"), parse_color("red")))
    'url(#grad) red'
    """

    iri: FuncIRI
    fallback: Color | PaintKeyword | None = None

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize the reference and its fallback.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places. Defaults to the library default precision.

        Returns
        -------
        str
            ``url(...)`` optionally followed by the fallback.

        Examples
        --------
        >>> from svgwriter.color import parse_paint
        >>> parse_paint("url(#grad) none").svg_value()
        'url(#grad) none'
        """
        text = self.iri.svg_value(precision)
        if self.fallback is not None:
            text += " " + (self.fallback.value if isinstance(self.fallback, PaintKeyword) else self.fallback.svg_value(precision))
        return text

    def __str__(self) -> str:
        return self.svg_value()


Paint: TypeAlias = Color | PaintKeyword | PaintRef
PaintValue: TypeAlias = Union[Paint, str, "Element", Sequence[float], None]
"""A paint: color (name, CSS text, 0-1 tuple or array), keyword, reference, element or ``None``."""


def parse_paint(text: str) -> Paint:
    """Parse a ``fill`` or ``stroke`` value.

    Parameters
    ----------
    text : str
        A keyword (``none``, ``currentColor``, ``inherit``), a color, or a
        ``url(#id)`` reference optionally followed by a fallback.

    Returns
    -------
    Color or PaintKeyword or PaintRef
        The parsed paint.

    Raises
    ------
    ValueError
        If the text is not a valid paint, or a fallback is itself a reference.

    See Also
    --------
    parse_color : Parse colors only.

    Examples
    --------
    >>> from svgwriter.color import parse_paint
    >>> parse_paint("none")
    <PaintKeyword.NONE: 'none'>
    >>> str(parse_paint("url(#grad) red"))
    'url(#grad) red'
    """
    source = text.strip()
    for keyword in PaintKeyword:
        if source == keyword.value:
            return keyword
    if source.startswith("url("):
        end = source.index(")") + 1
        iri = parse_func_iri(source[:end])
        if iri is None:
            raise ValueError(f"invalid paint reference: {text!r}")
        rest = source[end:].strip()
        fallback: Color | PaintKeyword | None = None
        if rest:
            parsed = parse_paint(rest)
            if isinstance(parsed, PaintRef):
                raise ValueError("a paint fallback cannot be another reference")
            fallback = parsed
        return PaintRef(iri, fallback)
    return parse_color(source)
