"""
Piping frames into an ``ffmpeg`` subprocess.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import tempfile
from collections.abc import Iterable, Iterator

from ..._internal._platform import find_executable, missing
from ..._internal._typing import AnyPath
from ...errors import FFmpegError, FFmpegNotFoundError
from ._constants import FFMPEG, OUTPUTS, STDERR_TAIL
from .frames import Frame

__all__ = ["encode", "find_ffmpeg", "input_args", "output_args"]




def find_ffmpeg(executable: str | None = None) -> str:
    """Full path of the ffmpeg executable.

    Parameters
    ----------
    executable : str, optional
        A name or path to look up. Defaults to ``SVGWRITER_FFMPEG``, else ``ffmpeg`` on ``PATH``.

    Returns
    -------
    str
        The resolved path.

    Raises
    ------
    FFmpegNotFoundError
        When it cannot be found; nothing has been rendered at that point.

    See Also
    --------
    encode : Needs the resolved executable.

    Examples
    --------
    >>> from svgwriter.errors import FFmpegNotFoundError
    >>> from svgwriter.motion.video import find_ffmpeg
    >>> try:
    ...     find_ffmpeg("no-such-ffmpeg")
    ... except FFmpegNotFoundError:
    ...     print("not found")
    not found
    """
    found = find_executable(executable or FFMPEG)
    if found is None:
        raise missing("ffmpeg", f"{executable or FFMPEG!r} was not found. Nothing was rendered. Video export",
                      FFmpegNotFoundError)
    return found


def output_args(path: AnyPath) -> list[str]:
    """Encoder arguments chosen from the output file's extension.

    Parameters
    ----------
    path : str or os.PathLike
        The output file.

    Returns
    -------
    list of str
        Arguments for ``.mp4``, ``.m4v``, ``.mov``, ``.webm``, ``.gif`` and
        ``.apng``; an empty list for any other extension, leaving ffmpeg to choose.

    See Also
    --------
    input_args : The matching input description.

    Examples
    --------
    >>> from svgwriter.motion.video._ffmpeg import output_args
    >>> output_args("clip.apng")
    ['-plays', '0', '-f', 'apng']
    >>> output_args("clip.xyz")
    []
    """
    return list(OUTPUTS.get(os.path.splitext(os.fspath(path))[1].lower(), []))


def input_args(first: Frame, fps: float) -> list[str]:
    """Arguments describing the piped input format.

    Parameters
    ----------
    first : Frame
        The first frame; its kind and size describe every frame.
    fps : float
        Input frame rate.

    Returns
    -------
    list of str
        PNG image pipe arguments, or raw RGBA arguments with the pixel size.

    See Also
    --------
    output_args : The matching output description.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter.motion.video.frames import to_frame
    >>> from svgwriter.motion.video._ffmpeg import input_args
    >>> frame = to_frame(0, 0.0, np.zeros((6, 8, 4), dtype="uint8"))
    >>> input_args(frame, 12)[:2], input_args(frame, 12)[-4:]
    (['-framerate', '12'], ['-s', '8x6', '-i', '-'])
    """
    rate = ["-framerate", f"{fps:g}"]
    if first.png:
        return [*rate, "-f", "image2pipe", "-c:v", "png", "-i", "-"]
    size = f"{first.width}x{first.height}"
    return [*rate, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", size, "-i", "-"]


def _checked(frames: Iterator[Frame], first: Frame) -> Iterator[Frame]:
    yield first
    for frame in frames:
        if (frame.png, frame.width, frame.height) != (first.png, first.width, first.height):
            raise ValueError(
                f"frame {frame.index} is {frame.width}x{frame.height}"
                f"{' PNG' if frame.png else ' RGBA'}; frame 0 was {first.width}x{first.height}"
                f"{' PNG' if first.png else ' RGBA'}"
            )
        yield frame


def _write(process: subprocess.Popen[bytes], data: bytes) -> bool:
    """Send one frame; ``False`` once ffmpeg has stopped reading."""
    assert process.stdin is not None
    try:
        process.stdin.write(data)
    except OSError:
        return False
    return True


def encode(frames: Iterable[Frame], path: AnyPath, fps: float, *, executable: str) -> None:
    """Run ffmpeg once, writing every frame to its stdin.

    Parameters
    ----------
    frames : iterable of Frame
        The frames; all must share kind and pixel size.
    path : str or os.PathLike
        Output file; the extension picks the encoder.
    fps : float
        Frame rate.
    executable : str
        Path of the ffmpeg executable, as from :func:`find_ffmpeg`.

    Raises
    ------
    ValueError
        If there are no frames, or a frame differs in kind or size from the first.
    FFmpegError
        If ffmpeg exits with a non-zero status.

    See Also
    --------
    svgwriter.motion.video.render_animation : Renders and encodes in one call.

    Examples
    --------
    >>> from svgwriter.motion.video._ffmpeg import encode
    >>> encode([], "out.gif", 12, executable="ffmpeg")
    Traceback (most recent call last):
    ...
    ValueError: no frames to encode
    """
    stream = iter(frames)
    first = next(stream, None)
    if first is None:
        raise ValueError("no frames to encode")
    command = [executable, "-y", "-loglevel", "error", *input_args(first, fps), *output_args(path), os.fspath(path)]
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=errors)
        assert process.stdin is not None
        try:
            for frame in _checked(stream, first):
                if not _write(process, frame.data):
                    break
        except BaseException:
            process.kill()
            process.wait()
            raise
        finally:
            with contextlib.suppress(OSError):
                process.stdin.close()
        code = process.wait()
        if code != 0:
            errors.seek(0)
            message = errors.read().decode("utf-8", "replace")[-STDERR_TAIL:]
            raise FFmpegError(f"ffmpeg exited with status {code}: {message.strip()}")
