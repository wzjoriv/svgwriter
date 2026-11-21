"""``<filter>`` and every SVG 1.1 filter primitive."""

from __future__ import annotations

from ._channels import FeFuncA, FeFuncB, FeFuncG, FeFuncR
from ._component import FeComponentTransfer
from ._compositing import BlendMode, CompositeOperator, FeBlend, FeComposite
from ._convolve import FeConvolveMatrix, FeGaussianBlur
from ._displacement import FeDisplacementMap, FeMorphology
from ._effects import Channel, ColorMatrixType, EdgeMode, FeColorMatrix, MorphologyOperator, TurbulenceType
from ._filter import Filter
from ._flood import FeFlood, FeImage
from ._merge import FeMerge, FeMergeNode
from ._offset import FeOffset, FeTile
from ._shading import FeDiffuseLighting, FeSpecularLighting
from ._turbulence import FeTurbulence
from .base import FilterInput, FilterPrimitive, SingleInput, StandardInput, TwoInputs, resolve_input
from .lighting import FeDistantLight, FePointLight, FeSpotLight, LightSource
from .transfer import FeFunc, TransferType

__all__ = [
    "BlendMode",
    "Channel",
    "ColorMatrixType",
    "CompositeOperator",
    "EdgeMode",
    "FeBlend",
    "FeColorMatrix",
    "FeComponentTransfer",
    "FeComposite",
    "FeConvolveMatrix",
    "FeDiffuseLighting",
    "FeDisplacementMap",
    "FeDistantLight",
    "FeFlood",
    "FeFunc",
    "FeFuncA",
    "FeFuncB",
    "FeFuncG",
    "FeFuncR",
    "FeGaussianBlur",
    "FeImage",
    "FeMerge",
    "FeMergeNode",
    "FeMorphology",
    "FeOffset",
    "FePointLight",
    "FeSpecularLighting",
    "FeSpotLight",
    "FeTile",
    "FeTurbulence",
    "Filter",
    "FilterInput",
    "FilterPrimitive",
    "LightSource",
    "MorphologyOperator",
    "SingleInput",
    "StandardInput",
    "TransferType",
    "TurbulenceType",
    "TwoInputs",
    "resolve_input",
]
