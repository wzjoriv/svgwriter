from functools import singledispatch

__all__ = ["format_value"]

@singledispatch
def format_value(value: object, precision: int = 4) -> str: ...
