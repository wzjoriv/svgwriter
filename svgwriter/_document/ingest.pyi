from typing import Protocol, TypeVar
from ..elements.core._element import Element

E = TypeVar('E', bound=Element)

class SupportsSVG(Protocol):
    ...
