"""
Frame data returned by renderers: PNG bytes or RGBA arrays.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Protocol, TypeAlias, runtime_checkable

from ._constants import PNG_SIGNATURE, PNG_SIZE_OFFSET, RGBA_CHANNELS, RGBA_DTYPE

__all__ = ["Frame", "FrameData", "RGBAArray", "frame_times", "to_frame"]


@runtime_checkable
class RGBAArray(Protocol):
    """An array of shape ``(height, width, 4)`` and dtype ``uint8``.

    NumPy arrays qualify, as does anything with ``shape`` and ``tobytes``.

    See Also
    --------
    Frame : What a renderer's output is wrapped into.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter.video import RGBAArray
    >>> isinstance(np.zeros((6, 8, 4), dtype="uint8"), RGBAArray)
    True
    """

    @property
    def shape(self) -> tuple[int, ...]: ...

    def tobytes(self) -> bytes: ...


FrameData: TypeAlias = bytes | bytearray | memoryview | RGBAArray
"""What a renderer returns for one frame."""


@dataclass(frozen=True, slots=True)
class Frame:
    """One rendered frame, ready for the encoder.

    Parameters
    ----------
    index : int
        Position in the sequence, starting at 0.
    seconds : float
        Sample time in seconds.
    width : int
        Width in pixels.
    height : int
        Height in pixels.
    data : bytes
        Encoded PNG bytes, or raw RGBA bytes when `png` is False.
    png : bool
        Whether `data` is a PNG file rather than raw pixels.

    See Also
    --------
    to_frame : Build a frame from renderer output.

    Examples
    --------
    >>> from svgwriter.video import Frame
    >>> frame = Frame(0, 0.0, 2, 1, bytes(8), png=False)
    >>> frame.width * frame.height * 4 == len(frame.data)
    True
    """

    index: int
    seconds: float
    width: int
    height: int
    data: bytes
    png: bool


def _png_size(data: bytes) -> tuple[int, int]:
    width, height = struct.unpack(">II", data[PNG_SIZE_OFFSET:PNG_SIZE_OFFSET + 8])
    return width, height


def to_frame(index: int, seconds: float, data: FrameData) -> Frame:
    """Check and wrap renderer output.

    Parameters
    ----------
    index : int
        Position of the frame in the sequence.
    seconds : float
        Sample time in seconds.
    data : bytes, bytearray, memoryview or RGBAArray
        PNG bytes or an ``(height, width, 4)`` uint8 array.

    Returns
    -------
    Frame
        The wrapped frame with its pixel size read from `data`.

    Raises
    ------
    TypeError
        If bytes are not a PNG, or `data` is of an unsupported type.
    ValueError
        If an array does not have shape ``(height, width, 4)`` and dtype uint8.

    See Also
    --------
    frame_times : The sample times passed as `seconds`.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter.video.frames import to_frame
    >>> frame = to_frame(0, 0.0, np.zeros((6, 8, 4), dtype="uint8"))
    >>> frame.width, frame.height, frame.png
    (8, 6, False)
    >>> to_frame(0, 0.0, b"abc")
    Traceback (most recent call last):
    ...
    TypeError: renderer returned bytes that are not a PNG; return PNG bytes or an RGBA array
    """
    if isinstance(data, (bytes, bytearray, memoryview)):
        raw = bytes(data)
        if not raw.startswith(PNG_SIGNATURE):
            raise TypeError("renderer returned bytes that are not a PNG; return PNG bytes or an RGBA array")
        width, height = _png_size(raw)
        return Frame(index, seconds, width, height, raw, True)
    if isinstance(data, RGBAArray):
        shape = tuple(data.shape)
        if len(shape) != 3 or shape[2] != RGBA_CHANNELS:
            raise ValueError(f"RGBA frames need shape (height, width, 4), got {shape}")
        dtype = getattr(data, "dtype", RGBA_DTYPE)
        if str(dtype) != RGBA_DTYPE:
            raise ValueError(f"RGBA frames need dtype uint8, got {dtype}")
        return Frame(index, seconds, int(shape[1]), int(shape[0]), data.tobytes(), False)
    raise TypeError(f"renderer returned {type(data).__name__}; expected PNG bytes or an RGBA array")


def frame_times(fps: float, duration: float) -> list[float]:
    """Sample times ``0, 1/fps, ...`` covering *duration* seconds.

    Parameters
    ----------
    fps : float
        Frames per second. Must be positive.
    duration : float
        Length in seconds. Must be positive.

    Returns
    -------
    list of float
        One time per frame; at least one.

    Raises
    ------
    ValueError
        If `fps` or `duration` is not positive.

    See Also
    --------
    iter_frames : Renders a frame at each of these times.

    Examples
    --------
    >>> from svgwriter.video import frame_times
    >>> frame_times(4, 1)
    [0.0, 0.25, 0.5, 0.75]
    """
    if fps <= 0:
        raise ValueError(f"fps must be positive, got {fps}")
    if duration <= 0:
        raise ValueError(f"duration must be positive, got {duration}")
    count = max(1, math.ceil(round(fps * duration, 9)))
    return [index / fps for index in range(count)]
