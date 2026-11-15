"""``style``, ``view`` and ``color-profile``."""

from __future__ import annotations

from typing import Any

from ...attributes.style import StyleSheet
from .._mixins import (
    CoreAttributes,
    ExternalResourcesAttribute,
    XLinkAttributes,
)
from .._viewport import FitToViewBox
from ..base import ContentModel, Element

__all__ = ["ColorProfile", "StyleElement", "View"]


class StyleElement(CoreAttributes, tag="style", content=ContentModel.TEXT):
    """``<style>``: an embedded style sheet."""

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
        self.text = css  # type: ignore[assignment]

    @property
    def text(self) -> str:
        return super().text

    @text.setter
    def text(self, value: str | StyleSheet) -> None:
        Element.text.fset(self, value.css() if isinstance(value, StyleSheet) else value)  # type: ignore[attr-defined]


class View(FitToViewBox, ExternalResourcesAttribute, CoreAttributes, tag="view", content=ContentModel.EMPTY):
    """``<view>``: a named view into the document."""

    def __init__(self, *, view_target: str | None = None, zoom_and_pan: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update(view_target=view_target, zoom_and_pan=zoom_and_pan)


class ColorProfile(XLinkAttributes, CoreAttributes, tag="color-profile", content=ContentModel.ELEMENTS):
    """``<color-profile>``: an ICC profile referenced by ``icc-color``."""

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
