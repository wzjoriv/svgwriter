from collections.abc import Iterable
from os import PathLike
from .frames import Frame

__all__ = [
    "FFmpegError",
    "FFmpegNotFoundError",
    "encode",
    "find_ffmpeg",
    "input_args",
    "output_args",
]

class FFmpegNotFoundError(RuntimeError):
    ...

class FFmpegError(RuntimeError):
    ...

def find_ffmpeg(executable: str | None = None) -> str: ...

def output_args(path: str | PathLike[str]) -> list[str]: ...

def input_args(first: Frame, fps: float) -> list[str]: ...

def encode(
    frames: Iterable[Frame],
    path: str | PathLike[str],
    fps: float,
    *,
    executable: str,
) -> None: ...
