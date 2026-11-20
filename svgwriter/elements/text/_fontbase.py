"""
Private bases of the SVG font elements and the glyph lookups of ``<font>``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._internal._typing import Self
from ...pathdata.builder import PathBuilder
from ...pathdata.data import PathData
from .._behavior._mixins import CoreAttributes, PresentationAttributes
from ..core._container import Container
from ..core._element import Category, Child, ContentModel, Element

if TYPE_CHECKING:
    from ._fonts import Glyph

__all__ = ["FontGlyphs"]


class _GlyphBase(PresentationAttributes, CoreAttributes, Container[Element], category=Category.FONT):
    def __init__(
        self,
        *children: Child,
        d: PathData | PathBuilder | str | None = None,
        horiz_adv_x: float | None = None,
        vert_origin_x: float | None = None,
        vert_origin_y: float | None = None,
        vert_adv_y: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*children, **kwargs)
        if isinstance(d, PathBuilder):
            d = d.build()
        elif isinstance(d, str):
            d = PathData(d)
        self.update(d=d, horiz_adv_x=horiz_adv_x, vert_origin_x=vert_origin_x, vert_origin_y=vert_origin_y, vert_adv_y=vert_adv_y)


class _Kern(CoreAttributes, category=Category.FONT, content=ContentModel.EMPTY):
    def __init__(
        self,
        k: float,
        *,
        u1: str | None = None,
        g1: str | None = None,
        u2: str | None = None,
        g2: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.update(u1=u1, g1=g1, u2=u2, g2=g2, k=k)

    @classmethod
    def pair(cls, first: str, second: str, k: float, **kwargs: Any) -> Self:
        """Create a kerning pair for two characters.

        Parameters
        ----------
        first : str
            The first character.
        second : str
            The second character.
        k : float
            The adjustment applied between them.
        **kwargs
            Further attributes.

        Returns
        -------
        HKern or VKern
            A kerning element of the calling class.

        Examples
        --------
        >>> from svgwriter.elements.text import HKern
        >>> str(HKern.pair("A", "V", -3))
        '<hkern u1="A" u2="V" k="-3"/>'
        """
        return cls(k, u1=first, u2=second, **kwargs)


class FontGlyphs:
    """Glyph lookups; mixed into :class:`~svgwriter.elements.Font`."""

    __slots__ = ()

    def glyph(self, unicode: str, d: PathData | PathBuilder | str, **kwargs: Any) -> Glyph:
        """Append a glyph and return it.

        Parameters
        ----------
        unicode : str
            The character sequence the glyph draws.
        d : PathData or PathBuilder or str
            The outline.
        **kwargs
            Further attributes of the :class:`Glyph`.

        Returns
        -------
        Glyph
            The new glyph, already a child of the font.

        Examples
        --------
        >>> from svgwriter.elements.text import Font
        >>> f = Font(horiz_adv_x=10)
        >>> str(f.glyph("a", "M0 0L5 5"))
        '<glyph d="M0 0 L5 5" unicode="a"/>'
        """
        from ._fonts import Glyph

        return self.add(Glyph(unicode, d, **kwargs))

    def glyphs(self) -> dict[str, Glyph]:
        """The font's glyphs keyed by their ``unicode`` attribute.

        Returns
        -------
        dict of str to Glyph
            Glyph children in document order.

        Examples
        --------
        >>> from svgwriter.elements.text import Font
        >>> f = Font()
        >>> _ = f.glyph("a", "M0 0L5 5")
        >>> list(f.glyphs())
        ['a']
        """
        from ._fonts import Glyph

        return {str(g.get("unicode")): g for g in self if isinstance(g, Glyph)}
