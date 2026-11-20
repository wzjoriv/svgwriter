from ._typing import ElementId

__all__ = ["IdFactory", "next_id"]

class IdFactory:
    def __init__(self) -> None: ...
    def __call__(self, prefix: str) -> ElementId: ...
    def reset(self) -> None: ...

next_id: IdFactory
