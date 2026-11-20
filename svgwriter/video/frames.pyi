from dataclasses import dataclass
from typing import Protocol, TypeAlias, runtime_checkable

__all__ = ["Frame", "FrameData", "RGBAArray", "frame_times", "to_frame"]

@runtime_checkable
class RGBAArray(Protocol):
    @property
    def shape(self) -> tuple[int, ...]: ...
    def tobytes(self) -> bytes: ...

FrameData: TypeAlias = bytes | bytearray | memoryview | RGBAArray

@dataclass(frozen=True, slots=True)
class Frame:
    index: int
    time: float
    width: int
    height: int
    data: bytes
    png: bool

    def __init__(
        self,
        index: int,
        time: float,
        width: int,
        height: int,
        data: bytes,
        png: bool,
    ) -> None: ...

def to_frame(
    index: int,
    time: float,
    data: FrameData,
) -> Frame: ...

def frame_times(fps: float, duration: float) -> list[float]: ...
