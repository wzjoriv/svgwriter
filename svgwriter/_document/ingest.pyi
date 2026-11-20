from typing import Any, Protocol, TypeVar
from ..elements.core import Element

E = TypeVar('E', bound=Element)

class SupportsSVG(Protocol):
    ...

def to_element(item: Any) -> Any: ...
