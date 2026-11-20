from ..elements.structure import Group

__all__ = ["latex"]

def latex(
    source: str,
    *,
    display: bool = False,
    preamble: str = '',
    engine: str = 'auto',
) -> Group: ...
