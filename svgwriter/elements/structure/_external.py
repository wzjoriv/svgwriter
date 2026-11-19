"""
``style``, ``view`` and ``color-profile``.
"""

from __future__ import annotations

from typing import Any

from ...attributes.style import StyleSheet
from .._mixins import (
    CoreAttributes,
    ExternalResourcesAttribute,
    XLinkAttributes,
)
from .._viewport import FitToViewBox
from ..base import ContentModel

__all__ = ["ColorProfile", "StyleElement", "View"]


class StyleElement(CoreAttributes, tag="style", content=ContentModel.TEXT):
    """``<style>``: an embedded style sheet.

    Parameters
    ----------
    css : str or StyleSheet, optional
        The style sheet text, or a :class:`~svgwriter.StyleSheet` to render.
        Defaults to empty.
    type : str, optional
        Style language. Defaults to ``"text/css"``.
    media : str, optional
        Media query the sheet applies to. Defaults to None.
    title : str, optional
        Alternate style sheet title. Defaults to None.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.StyleElement("circle { fill: red }"))
    '<style type="text/css">circle { fill: red }</style>'
    """

    def __init__(
        self,
        css: str | StyleSheet = "",
        *,
        type: str = "text/css",
        media: str | None = None,
        title: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.update(type=type, media=media, title=title)
        self.css = css  # type: ignore[assignment]

    @property
    def css(self) -> str:
        """The style sheet text; assign a string or a :class:`~svgwriter.StyleSheet`.

        Examples
        --------
        >>> import svgwriter as svg
        >>> style = svg.StyleElement()
        >>> style.css = "rect { fill: blue }"
        >>> style.css
        'rect { fill: blue }'
        """
        return self.text_content

    @css.setter
    def css(self, value: str | StyleSheet) -> None:
        self.text_content = value.css() if isinstance(value, StyleSheet) else value


class View(FitToViewBox, ExternalResourcesAttribute, CoreAttributes, tag="view", content=ContentModel.EMPTY):
    """``<view>``: a named view into the document.

    Parameters
    ----------
    view_target : str, optional
        Elements the view targets. Defaults to None.
    zoom_and_pan : str, optional
        ``"magnify"`` or ``"disable"``. Defaults to None.
    **kwargs
        ``view_box``, ``preserve_aspect_ratio``, core and other SVG
        attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.View(id="zoomed", view_box=(0, 0, 50, 50)))
    '<view id="zoomed" viewBox="0 0 50 50"/>'
    """

    def __init__(self, *, view_target: str | None = None, zoom_and_pan: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update(view_target=view_target, zoom_and_pan=zoom_and_pan)


class ColorProfile(XLinkAttributes, CoreAttributes, tag="color-profile", content=ContentModel.ELEMENTS):
    """``<color-profile>``: an ICC profile referenced by ``icc-color``.

    Parameters
    ----------
    name : str
        Name used to refer to the profile from ``icc-color``.
    href : str, optional
        Location of the profile. Defaults to None.
    local : str, optional
        Name of a locally installed profile. Defaults to None.
    rendering_intent : str, optional
        Rendering intent, such as ``"perceptual"``. Defaults to None.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.ColorProfile("sRGB", "srgb.icc"))
    '<color-profile xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="srgb.icc" name="sRGB"/>'
    """

    def __init__(
        self,
        name: str,
        href: str | None = None,
        *,
        local: str | None = None,
        rendering_intent: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(href=href, **kwargs)
        self.update(local=local, name=name, rendering_intent=rendering_intent)
