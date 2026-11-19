"""
SVG fonts: ``font``, glyphs, kerning and ``font-face``.
"""

from __future__ import annotations

from typing import Any

from .._internal._typing import Self
from ..pathdata.builder import PathBuilder
from ..pathdata.data import PathData
from ._mixins import CoreAttributes, ExternalResourcesAttribute, PresentationAttributes, XLinkAttributes
from .base import Category, Child, ContentModel, Element
from .container import Container

__all__ = [
    "Font",
    "FontFace",
    "FontFaceFormat",
    "FontFaceName",
    "FontFaceSrc",
    "FontFaceUri",
    "Glyph",
    "HKern",
    "MissingGlyph",
    "VKern",
]


class Font(PresentationAttributes, ExternalResourcesAttribute, CoreAttributes, Container[Element], tag="font", category=Category.FONT):
    """``<font>``: an SVG font made of glyph outlines.

    Parameters
    ----------
    *children : Element
        Glyphs, kerning pairs and a ``font-face``.
    horiz_adv_x : float, optional
        Default horizontal advance of glyphs. Defaults to 0.
    horiz_origin_x, horiz_origin_y : float, optional
        Origin for horizontal text.
    vert_origin_x, vert_origin_y : float, optional
        Origin for vertical text.
    vert_adv_y : float, optional
        Default vertical advance of glyphs.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    FontFace : The font's descriptors.
    Glyph : One character outline.

    Examples
    --------
    >>> f = Font(horiz_adv_x=10)
    >>> str(f)
    '<font horiz-adv-x="10"/>'
    """

    def __init__(
        self,
        *children: Child,
        horiz_adv_x: float = 0,
        horiz_origin_x: float | None = None,
        horiz_origin_y: float | None = None,
        vert_origin_x: float | None = None,
        vert_origin_y: float | None = None,
        vert_adv_y: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*children, **kwargs)
        self.update(
            horiz_origin_x=horiz_origin_x,
            horiz_origin_y=horiz_origin_y,
            horiz_adv_x=horiz_adv_x,
            vert_origin_x=vert_origin_x,
            vert_origin_y=vert_origin_y,
            vert_adv_y=vert_adv_y,
        )

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
        >>> f = Font(horiz_adv_x=10)
        >>> str(f.glyph("a", "M0 0L5 5"))
        '<glyph d="M0 0 L5 5" unicode="a"/>'
        """
        return self.add(Glyph(unicode, d, **kwargs))

    def glyphs(self) -> dict[str, Glyph]:
        """The font's glyphs keyed by their ``unicode`` attribute.

        Returns
        -------
        dict of str to Glyph
            Glyph children in document order.

        Examples
        --------
        >>> f = Font()
        >>> _ = f.glyph("a", "M0 0L5 5")
        >>> list(f.glyphs())
        ['a']
        """
        return {str(g.get("unicode")): g for g in self if isinstance(g, Glyph)}


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


class Glyph(_GlyphBase, tag="glyph"):
    """``<glyph>``: the outline for one character sequence.

    Parameters
    ----------
    unicode : str, optional
        The character sequence the glyph draws.
    d : PathData or PathBuilder or str, optional
        The outline.
    glyph_name : str, optional
        A name to refer to the glyph by.
    orientation : str, optional
        ``"h"`` or ``"v"`` to restrict the glyph to one writing direction.
    arabic_form : str, optional
        Contextual form for Arabic.
    lang : str, optional
        Language the glyph applies to.
    **kwargs
        ``horiz_adv_x``, ``vert_origin_x``, ``vert_origin_y``, ``vert_adv_y`` and
        other presentation, core and SVG attributes in Python spelling.

    See Also
    --------
    MissingGlyph : The fallback glyph.

    Examples
    --------
    >>> str(Glyph("a", "M0 0L5 5", horiz_adv_x=6))
    '<glyph d="M0 0 L5 5" horiz-adv-x="6" unicode="a"/>'
    """

    def __init__(
        self,
        unicode: str | None = None,
        d: PathData | PathBuilder | str | None = None,
        *,
        glyph_name: str | None = None,
        orientation: str | None = None,
        arabic_form: str | None = None,
        lang: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(d=d, **kwargs)
        self.update(unicode=unicode, glyph_name=glyph_name, orientation=orientation, arabic_form=arabic_form, lang=lang)


class MissingGlyph(_GlyphBase, tag="missing-glyph"):
    """``<missing-glyph>``: drawn for characters without a glyph.

    Parameters
    ----------
    *children : Element
        Graphics, as an alternative to ``d``.
    d : PathData or PathBuilder or str, optional
        The outline.
    horiz_adv_x : float, optional
        Horizontal advance.
    vert_origin_x, vert_origin_y : float, optional
        Origin for vertical text.
    vert_adv_y : float, optional
        Vertical advance.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Glyph : A glyph for a specific character.

    Examples
    --------
    >>> str(MissingGlyph(d="M0 0"))
    '<missing-glyph d="M0 0"/>'
    """


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
        >>> str(HKern.pair("A", "V", -3))
        '<hkern u1="A" u2="V" k="-3"/>'
        """
        return cls(k, u1=first, u2=second, **kwargs)


class HKern(_Kern, tag="hkern"):
    """``<hkern>``: horizontal kerning pair.

    Parameters
    ----------
    k : float
        The adjustment applied between the pair.
    u1, u2 : str, optional
        Unicode characters or ranges of the first and second glyph.
    g1, g2 : str, optional
        Glyph names of the first and second glyph.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    VKern : Vertical kerning.

    Examples
    --------
    >>> str(HKern(-3, u1="A", u2="V"))
    '<hkern u1="A" u2="V" k="-3"/>'
    """


class VKern(_Kern, tag="vkern"):
    """``<vkern>``: vertical kerning pair.

    Parameters
    ----------
    k : float
        The adjustment applied between the pair.
    u1, u2 : str, optional
        Unicode characters or ranges of the first and second glyph.
    g1, g2 : str, optional
        Glyph names of the first and second glyph.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    HKern : Horizontal kerning.

    Examples
    --------
    >>> str(VKern(2, u1="a", u2="b"))
    '<vkern u1="a" u2="b" k="2"/>'
    """


class FontFace(CoreAttributes, Container[Element], tag="font-face", category=Category.FONT):
    """``<font-face>``: font descriptors, mirroring CSS ``@font-face``.

    Less common descriptors (``panose_1``, ``v_alphabetic``,
    ``underline_position`` and so on) go through ``**descriptors``.

    Parameters
    ----------
    *children : Element
        A ``font-face-src`` and similar.
    font_family, font_style, font_variant, font_weight, font_stretch, font_size : str, optional
        The matching CSS descriptors.
    unicode_range : str, optional
        Characters the face covers.
    units_per_em : float, optional
        The em square in glyph units.
    ascent, descent, cap_height, x_height : float, optional
        Vertical metrics in glyph units.
    **descriptors
        Further descriptors and core attributes in Python spelling.

    See Also
    --------
    FontFaceSrc : Where the font data comes from.

    Examples
    --------
    >>> str(FontFace(font_family="X", units_per_em=1000))
    '<font-face font-family="X" units-per-em="1000"/>'
    """

    def __init__(
        self,
        *children: Child,
        font_family: str | None = None,
        font_style: str | None = None,
        font_variant: str | None = None,
        font_weight: str | None = None,
        font_stretch: str | None = None,
        font_size: str | None = None,
        unicode_range: str | None = None,
        units_per_em: float | None = None,
        ascent: float | None = None,
        descent: float | None = None,
        cap_height: float | None = None,
        x_height: float | None = None,
        **descriptors: Any,
    ) -> None:
        super().__init__(*children, **descriptors)
        self.update(
            font_family=font_family,
            font_style=font_style,
            font_variant=font_variant,
            font_weight=font_weight,
            font_stretch=font_stretch,
            font_size=font_size,
            unicode_range=unicode_range,
            units_per_em=units_per_em,
            ascent=ascent,
            descent=descent,
            cap_height=cap_height,
            x_height=x_height,
        )


class FontFaceSrc(CoreAttributes, Container[Element], tag="font-face-src", category=Category.FONT):
    """``<font-face-src>``: where the font data comes from.

    Parameters
    ----------
    *children : Element
        :class:`FontFaceUri` and :class:`FontFaceName` entries, in order of preference.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    FontFace : The descriptor element that contains it.

    Examples
    --------
    >>> str(FontFaceSrc(FontFaceName("X")))
    '<font-face-src><font-face-name name="X"/></font-face-src>'
    """


class FontFaceFormat(CoreAttributes, tag="font-face-format", category=Category.FONT, content=ContentModel.EMPTY):
    """``<font-face-format>``: the format of a ``font-face-uri``.

    Parameters
    ----------
    string : str, optional
        The format hint, such as ``"svg"``.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    FontFaceUri : The element it describes.

    Examples
    --------
    >>> str(FontFaceFormat("svg"))
    '<font-face-format string="svg"/>'
    """

    def __init__(self, string: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update(string=string)


class FontFaceUri(XLinkAttributes, CoreAttributes, Container[FontFaceFormat], tag="font-face-uri", category=Category.FONT):
    """``<font-face-uri>``: an external font reference.

    Parameters
    ----------
    href : str, optional
        Location of the font.
    *formats : FontFaceFormat
        Format hints.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    FontFaceName : A locally installed font instead.

    Examples
    --------
    >>> len(FontFaceUri("a.svg", FontFaceFormat("svg")))
    1
    """

    def __init__(self, href: str | None = None, *formats: FontFaceFormat, **kwargs: Any) -> None:
        super().__init__(*formats, href=href, **kwargs)


class FontFaceName(CoreAttributes, tag="font-face-name", category=Category.FONT, content=ContentModel.EMPTY):
    """``<font-face-name>``: a locally installed font by name.

    Parameters
    ----------
    name : str, optional
        The font's name.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    FontFaceUri : An external font instead.

    Examples
    --------
    >>> str(FontFaceName("X"))
    '<font-face-name name="X"/>'
    """

    def __init__(self, name: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update(name=name)
