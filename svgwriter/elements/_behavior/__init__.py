"""
Behaviour shared by many element classes: attribute groups, transforms, geometry and conversions.
"""

from __future__ import annotations

from ._convert import Convertible
from ._geometry import PathOperand
from ._mixins import (
    ConditionalAttributes,
    CoreAttributes,
    ExternalResourcesAttribute,
    GraphicsElement,
    PresentationAttributes,
    StyleAttributes,
    Transformable,
    XLinkAttributes,
    XmlSpace,
)
from ._viewport import FitToViewBox, Positioned

__all__ = [
    "ConditionalAttributes",
    "Convertible",
    "CoreAttributes",
    "ExternalResourcesAttribute",
    "FitToViewBox",
    "GraphicsElement",
    "PathOperand",
    "Positioned",
    "PresentationAttributes",
    "StyleAttributes",
    "Transformable",
    "XLinkAttributes",
    "XmlSpace",
]
