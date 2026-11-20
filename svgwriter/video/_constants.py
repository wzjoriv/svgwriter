"""
Constants for ``svgwriter.video``: defaults, tables and patterns.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "CHANNELS",
    "CHANNEL_MAX",
    "CLOCK_RE",
    "DURATION_RE",
    "EPSILON",
    "EVEN_PAD",
    "FFMPEG",
    "FPS_RE",
    "GIF_FILTER",
    "INDEFINITE",
    "NUMBER_RE",
    "OUTPUTS",
    "PNG_SIGNATURE",
    "PNG_SIZE_OFFSET",
    "RGBA_CHANNELS",
    "RGBA_DTYPE",
    "SECONDS_PER_HOUR",
    "SECONDS_PER_MINUTE",
    "STDERR_TAIL",
    "STREAM_RE",
    "TIMECOUNT_RE",
    "TIME_SCALE",
]

FFMPEG: Final = "ffmpeg"
STDERR_TAIL: Final = 2000
EVEN_PAD: Final = "pad=ceil(iw/2)*2:ceil(ih/2)*2"
GIF_FILTER: Final = "split[a][b];[a]palettegen=reserve_transparent=1[p];[b][p]paletteuse"
OUTPUTS: Final = {
    ".mp4": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", EVEN_PAD, "-movflags", "+faststart"],
    ".m4v": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", EVEN_PAD],
    ".mov": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", EVEN_PAD],
    ".webm": ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p"],
    ".gif": ["-filter_complex", GIF_FILTER, "-loop", "0"],
    ".apng": ["-plays", "0", "-f", "apng"],
}

TIMECOUNT_RE: Final = re.compile(r"^\s*([+-]?\d*\.?\d+)\s*(ms|s|min|h)?\s*$")
CLOCK_RE: Final = re.compile(r"^\s*(?:(\d+):)?(\d{1,2}):(\d{1,2}(?:\.\d+)?)\s*$")
TIME_SCALE: Final = {"ms": 0.001, "s": 1.0, "min": 60.0, "h": 3600.0, None: 1.0}
NUMBER_RE: Final = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
SECONDS_PER_MINUTE: Final = 60.0
SECONDS_PER_HOUR: Final = 3600.0
INDEFINITE: Final = "indefinite"
EPSILON: Final = 1e-9


PNG_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"
PNG_SIZE_OFFSET: Final = 16
RGBA_CHANNELS: Final = 4
RGBA_DTYPE: Final = "uint8"

CHANNELS: Final = 4
CHANNEL_MAX: Final = 255.0
STREAM_RE: Final = re.compile(r"Stream #\S+.*?Video:.*?(\d{2,5})x(\d{2,5})")
FPS_RE: Final = re.compile(r"(\d+(?:\.\d+)?) (?:fps|tbr)")
DURATION_RE: Final = re.compile(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)")
