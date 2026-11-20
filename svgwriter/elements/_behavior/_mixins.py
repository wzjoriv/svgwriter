"""
Attribute groups shared by many elements (SVG 1.1, appendix M).

Each group is a cooperative base: it takes its own keywords and forwards
the rest with ``super().__init__(*args, **kwargs)``.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from typing import Any

from ..._internal._typing import FillRule, LineCap, LineJoin, Opacity
from ...attributes.descriptors import Attr, LengthAttr
from ...attributes.length import LengthLike
from ...attributes.style import Style, StyleLike
from ...color.paint import PaintValue, parse_paint
from ..core._element import Child, Element
from ._convert import Convertible
from ._styling import PresentationMethods, StyleMethods
from ._transformable import Transformable

__all__ = [
    "ConditionalAttributes",
    "CoreAttributes",
    "ExternalResourcesAttribute",
    "GraphicsElement",
    "PresentationAttributes",
    "StyleAttributes",
    "Transformable",
    "XLinkAttributes",
    "XmlSpace",
]


class XmlSpace(str, enum.Enum):
    """Values of ``xml:space``: whether whitespace is collapsed or kept.

    Examples
    --------
    >>> from svgwriter.elements._behavior import XmlSpace
    >>> XmlSpace.PRESERVE.value
    'preserve'
    """

    DEFAULT = "default"
    PRESERVE = "preserve"


def _words(value: str | Sequence[str] | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return " ".join(value)


class CoreAttributes(Element):
    """``id``, ``xml:base``, ``xml:lang`` and ``xml:space``.

    Parameters
    ----------
    *args : Element or str
        Children.
    xml_base : str, optional
        Base URI for relative references. Defaults to None.
    xml_lang : str, optional
        Language of the element's content. Defaults to None.
    xml_space : XmlSpace, optional
        Whitespace handling. Defaults to None.
    **kwargs
        Passed on to the next base class.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.group(xml_lang="en").get("xml:lang")
    'en'
    """

    def __init__(
        self,
        *args: Child,
        xml_base: str | None = None,
        xml_lang: str | None = None,
        xml_space: XmlSpace | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.update(xml_base=xml_base, xml_lang=xml_lang, xml_space=xml_space)


class ConditionalAttributes(Element):
    """``requiredFeatures``, ``requiredExtensions`` and ``systemLanguage``.

    Parameters
    ----------
    *args : Element or str
        Children.
    required_features : str or sequence of str, optional
        Feature strings, joined by spaces. Defaults to None.
    required_extensions : str or sequence of str, optional
        Extension URIs, joined by spaces. Defaults to None.
    system_language : str or sequence of str, optional
        Language tags, joined by commas. Defaults to None.
    **kwargs
        Passed on to the next base class.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.group(system_language=["en", "fr"]).get("systemLanguage")
    'en,fr'
    """

    def __init__(
        self,
        *args: Child,
        required_features: str | Sequence[str] | None = None,
        required_extensions: str | Sequence[str] | None = None,
        system_language: str | Sequence[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            required_features=_words(required_features),
            required_extensions=_words(required_extensions),
            system_language=",".join(system_language) if isinstance(system_language, (list, tuple)) else system_language,
        )


class StyleAttributes(StyleMethods, Element):
    """``class`` and ``style``.

    Parameters
    ----------
    *args : Element or str
        Children.
    class_ : str or sequence of str, optional
        Class names. Defaults to None.
    style : Style, mapping or str, optional
        Inline CSS declarations. Defaults to None.
    **kwargs
        Passed on to the next base class.

    Examples
    --------
    >>> import svgwriter as svg
    >>> g = svg.group(class_=["a", "b"], style="fill: red")
    >>> g.classes, g.style["fill"]
    (['a', 'b'], 'red')
    """

    def __init__(
        self,
        *args: Child,
        class_: str | Sequence[str] | None = None,
        style: StyleLike | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.update(class_=_words(class_))
        if style is not None:
            self.style = Style(style)


class PresentationAttributes(PresentationMethods, StyleAttributes):
    """The presentation attributes, plus moving them to and from CSS.

    Common properties are explicit keywords; any other presentation
    attribute can be passed through ``**kwargs``.

    Parameters
    ----------
    *args : Element or str
        Children.
    fill, stroke : color, str or Element, optional
        Paint for the interior and the outline. Defaults to None.
    fill_opacity, stroke_opacity, opacity : float, optional
        Opacity from 0 to 1. Defaults to None.
    fill_rule : {"nonzero", "evenodd"}, optional
        Interior rule. Defaults to None.
    stroke_width : length, optional
        Outline width. Defaults to None.
    stroke_linecap : {"butt", "round", "square"}, optional
        Shape of line ends. Defaults to None.
    stroke_linejoin : {"miter", "round", "bevel"}, optional
        Shape of line corners. Defaults to None.
    stroke_miterlimit : float, optional
        Miter length limit. Defaults to None.
    stroke_dasharray : sequence of float or str, optional
        Dash pattern. Defaults to None.
    stroke_dashoffset : length, optional
        Start of the dash pattern. Defaults to None.
    display, visibility : str, optional
        Rendering switches. Defaults to None.
    color : str, optional
        The ``currentColor`` value. Defaults to None.
    clip_path, mask, filter : str or Element, optional
        Reference to a clip path, mask or filter. Defaults to None.
    font_family, font_weight, text_anchor : str, optional
        Text properties; *font_weight* may also be an int. Defaults to None.
    font_size : length, optional
        Text size. Defaults to None.
    **kwargs
        Passed on to the next base class.

    Examples
    --------
    >>> import svgwriter as svg
    >>> r = svg.rect(0, 0, 1, 1, fill="red", stroke_width=2)
    >>> r.get("fill"), r.stroke_width
    ('red', 2.0)
    """

    fill = Attr[PaintValue](convert=parse_paint)
    stroke = Attr[PaintValue](convert=parse_paint)
    stroke_width = LengthAttr()
    opacity = Attr[float](convert=float)

    def __init__(
        self,
        *args: Child,
        fill: PaintValue = None,
        fill_opacity: Opacity | None = None,
        fill_rule: FillRule | None = None,
        stroke: PaintValue = None,
        stroke_width: LengthLike | None = None,
        stroke_opacity: Opacity | None = None,
        stroke_linecap: LineCap | None = None,
        stroke_linejoin: LineJoin | None = None,
        stroke_miterlimit: float | None = None,
        stroke_dasharray: Sequence[float] | str | None = None,
        stroke_dashoffset: LengthLike | None = None,
        opacity: Opacity | None = None,
        display: str | None = None,
        visibility: str | None = None,
        color: str | None = None,
        clip_path: str | Element | None = None,
        mask: str | Element | None = None,
        filter: str | Element | None = None,
        font_family: str | None = None,
        font_size: LengthLike | None = None,
        font_weight: str | int | None = None,
        text_anchor: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            fill=fill,
            fill_opacity=fill_opacity,
            fill_rule=fill_rule,
            stroke=stroke,
            stroke_width=stroke_width,
            stroke_opacity=stroke_opacity,
            stroke_linecap=stroke_linecap,
            stroke_linejoin=stroke_linejoin,
            stroke_miterlimit=stroke_miterlimit,
            stroke_dasharray=tuple(stroke_dasharray) if isinstance(stroke_dasharray, (list, tuple)) else stroke_dasharray,
            stroke_dashoffset=stroke_dashoffset,
            opacity=opacity,
            display=display,
            visibility=visibility,
            color=color,
            clip_path=clip_path,
            mask=mask,
            filter=filter,
            font_family=font_family,
            font_size=font_size,
            font_weight=font_weight,
            text_anchor=text_anchor,
        )


class XLinkAttributes(Element):
    """``xlink:href`` and the other XLink attributes.

    Parameters
    ----------
    *args : Element or str
        Children.
    href : str or Element, optional
        The link target; an element becomes a ``#id`` reference. Defaults to None.
    xlink_title, xlink_show, xlink_actuate, xlink_role, xlink_arcrole : str, optional
        The remaining XLink attributes. Defaults to None.
    **kwargs
        Passed on to the next base class.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.a(href="#a").target
    'a'
    """

    def __init__(
        self,
        *args: Child,
        href: str | Element | None = None,
        xlink_title: str | None = None,
        xlink_show: str | None = None,
        xlink_actuate: str | None = None,
        xlink_role: str | None = None,
        xlink_arcrole: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            xlink_href=href,
            xlink_title=xlink_title,
            xlink_show=xlink_show,
            xlink_actuate=xlink_actuate,
            xlink_role=xlink_role,
            xlink_arcrole=xlink_arcrole,
        )

    @property
    def href(self) -> Any:
        """This element's ``xlink:href``: the IRI or URL it points at, ``None`` when unset.

        Assign an element, an IRI or a string to change it.

        Examples
        --------
        >>> import svgwriter as svg
        >>> track = svg.path("M0 0 L10 10", id="track")
        >>> str(svg.Use(track).href)
        '#track'
        """
        return self.attributes.get("xlink:href")

    @href.setter
    def href(self, value: Any) -> None:
        self.set("xlink:href", value)

    @property
    def target(self) -> str | None:
        """The referenced id for local ``#id`` links.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.a(href="#a").target
        'a'
        """
        raw = self.attributes.get("xlink:href")
        text = None if raw is None else str(raw)
        return text[1:] if text and text.startswith("#") else None


class ExternalResourcesAttribute(Element):
    """``externalResourcesRequired``.

    Parameters
    ----------
    *args : Element or str
        Children.
    external_resources_required : bool, optional
        Whether external resources must load for the document to render.
        Defaults to None.
    **kwargs
        Passed on to the next base class.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.group(external_resources_required=True).get("externalResourcesRequired")
    True
    """

    def __init__(self, *args: Child, external_resources_required: bool | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update(external_resources_required=external_resources_required)


class GraphicsElement(
    Convertible,
    ExternalResourcesAttribute,
    PresentationAttributes,
    ConditionalAttributes,
    CoreAttributes,
):
    """Rendered element carrying every common attribute group.

    Combines the core, conditional, presentation and external-resource
    attributes with transforms and conversions; its parameters are those
    of the groups it combines.

    Examples
    --------
    >>> import svgwriter as svg
    >>> issubclass(svg.Rect, svg.elements.GraphicsElement)
    True
    """
