from collections.abc import Sequence
from typing import TypeAlias
from numpy import ndarray
from ..elements.filters import BlendMode, CompositeOperator

__all__ = ["Operator", "composite_rgba", "resolve_operator"]

Operator: TypeAlias = CompositeOperator | BlendMode | str

def resolve_operator(operator: Operator) -> CompositeOperator | BlendMode: ...

def composite_rgba(
    source: ndarray,
    backdrop: ndarray,
    operator: Operator = CompositeOperator.OVER,
    *,
    k: Sequence[float] = (),
) -> ndarray: ...
