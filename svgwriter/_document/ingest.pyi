from typing import Final, Protocol, TypeVar
from ..elements.base import Element

NON_CONTENT: Final = ...
E = TypeVar('E', bound=Element)

class SupportsSVG(Protocol):
    ...

RASTER_REPRS: Final = ...
