"""
Behaviour shared by many element classes: attribute groups, transforms, geometry and conversions.
"""

from __future__ import annotations

from ._convert import Convertible
from ._geometry import Operand, PathOperand, union_outline
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
from ._transformable import children_bbox, offset
from ._viewport import FitToViewBox, Positioned, positioned_bbox, user_units

__all__ = [
    "ConditionalAttributes",
    "Convertible",
    "CoreAttributes",
    "ExternalResourcesAttribute",
    "FitToViewBox",
    "GraphicsElement",
    "Operand",
    "PathOperand",
    "Positioned",
    "PresentationAttributes",
    "StyleAttributes",
    "Transformable",
    "XLinkAttributes",
    "XmlSpace",
    "children_bbox",
    "offset",
    "positioned_bbox",
    "union_outline",
    "user_units",
]
