from typing import Protocol, TypeVar
from ..elements.base import Element

E = TypeVar('E', bound=Element)

class SupportsSVG(Protocol):
    ...
