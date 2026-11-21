"""
Reading video: frames decoded lazily through ffmpeg as numpy arrays or ``<image>`` elements.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator
from fractions import Fraction
from typing import TYPE_CHECKING

import numpy as np

from ._constants import (
    CHANNELS,
    DURATION_RE,
    FPS_RE,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
    STREAM_RE,
)
from ._ffmpeg import FFmpegError, find_ffmpeg

if TYPE_CHECKING:
    from ..._internal._typing import AnyPath
    from ...model.elements.structure import Image

__all__ = ["Video"]


class Video:
    """A video file read lazily: ``video[i]`` is frame *i* as an ``<image>``.

    Frames are decoded on demand by ffmpeg (seeking for single frames, one
    stream for iteration), so long videos cost nothing until used. Combine
    footage with vector graphics in an animation ``update`` callback, for
    instance ``backdrop.pixels = video.at(seconds).pixels``.

    Parameters
    ----------
    path : str or os.PathLike
        Any file ffmpeg can read (mp4, webm, mov, gif, ...).
    ffmpeg : str, optional
        The ffmpeg executable. Defaults to None (found on ``PATH`` or ``SVGWRITER_FFMPEG``).

    Attributes
    ----------
    width, height : int
        Frame size in pixels.
    fps : float
        Frames per second.
    duration : float
        Length in seconds.

    Raises
    ------
    FFmpegNotFoundError
        If ffmpeg is not installed.
    FFmpegError
        If the file has no video stream ffmpeg can read.

    See Also
    --------
    svgwriter.Document.render_animation : The other direction, drawings into video.

    Examples
    --------
    >>> from svgwriter.motion.video import Video
    >>> # clip = Video("clip.mp4"); first = clip[0]; len(clip), clip.fps
    """

    def __init__(self, path: AnyPath, *, ffmpeg: str | None = None) -> None:
        self.path = os.fspath(path)
        self._ffmpeg = find_ffmpeg(ffmpeg)
        probe = subprocess.run([self._ffmpeg, "-hide_banner", "-i", self.path], capture_output=True, check=False)
        info = probe.stderr.decode("utf-8", "replace")
        size = STREAM_RE.search(info)
        if size is None:
            raise FFmpegError(f"no video stream in {self.path!r}: {info.strip().splitlines()[-1] if info.strip() else ''}")
        self.width, self.height = int(size.group(1)), int(size.group(2))
        rate = FPS_RE.search(info[size.start():])
        self.fps = float(Fraction(rate.group(1))) if rate else 25.0
        length = DURATION_RE.search(info)
        self.duration = (int(length.group(1)) * SECONDS_PER_HOUR + int(length.group(2)) * SECONDS_PER_MINUTE
                         + float(length.group(3))) if length else 0.0

    def __len__(self) -> int:
        """Number of frames (from the duration and frame rate)."""
        return max(int(round(self.duration * self.fps)), 0)

    def _decode(self, arguments: list[str]) -> subprocess.Popen[bytes]:
        command = [self._ffmpeg, "-v", "error", *arguments, "-f", "rawvideo", "-pix_fmt", "rgba", "-"]
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def frame(self, index: int) -> np.ndarray:
        """Frame *index* as a ``uint8`` ``(height, width, 4)`` RGBA array.

        Parameters
        ----------
        index : int
            Zero-based frame number; negative counts from the end.

        Returns
        -------
        numpy.ndarray
            The decoded pixels.

        Raises
        ------
        IndexError
            If there is no such frame.
        """
        count = len(self)
        if not -count <= index < count:
            raise IndexError(f"the video has {count} frames, not frame {index}")
        return self.array_at((index % count) / self.fps)

    def array_at(self, seconds: float) -> np.ndarray:
        """The frame shown at *seconds* as a ``uint8`` RGBA array (the last frame past the end)."""
        when = min(max(seconds, 0.0), max(self.duration - 1 / self.fps, 0.0))
        process = self._decode(["-ss", f"{when:.6f}", "-i", self.path, "-frames:v", "1"])
        data, error = process.communicate()
        size = self.width * self.height * CHANNELS
        if len(data) < size:
            raise FFmpegError(error.decode("utf-8", "replace").strip() or f"no frame at {seconds}s")
        return np.frombuffer(data[:size], np.uint8).reshape(self.height, self.width, CHANNELS)

    def at(self, seconds: float) -> Image:
        """The frame shown at *seconds* as an ``<image>`` at pixel size, placed at the origin."""
        from ...model.elements.structure import Image

        return Image(self.array_at(seconds))

    def __getitem__(self, index: int) -> Image:
        """``video[i]``: frame *i* as an ``<image>``."""
        from ...model.elements.structure import Image

        return Image(self.frame(index))

    def __iter__(self) -> Iterator[np.ndarray]:
        """Every frame in order as ``uint8`` RGBA arrays, decoded in one stream."""
        process = self._decode(["-i", self.path])
        size = self.width * self.height * CHANNELS
        assert process.stdout is not None
        try:
            while chunk := process.stdout.read(size):
                if len(chunk) < size:
                    break
                yield np.frombuffer(chunk, np.uint8).reshape(self.height, self.width, CHANNELS)
        finally:
            process.stdout.close()
            process.wait()

    def __repr__(self) -> str:
        return f"Video({self.path!r}, {self.width}x{self.height}, {self.fps:g} fps, {len(self)} frames)"
